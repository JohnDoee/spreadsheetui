from timeoutthreadpoolexecutor import TimeoutThreadPoolExecutor  # isort:skip
from concurrent.futures import thread  # isort:skip

thread.ThreadPoolExecutor = TimeoutThreadPoolExecutor  # isort:skip

import asyncio  # isort:skip
import daphne.server  # isort:skip
from twisted.internet import reactor  # isort:skip

asyncio.set_event_loop(reactor._asyncioEventloop)  # isort:skip


import os
import sys
import threading
import time
from pathlib import Path

import django
import toml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from channels.routing import get_default_application
from loguru import logger
from txasgiresource import ASGIResource
from zope.interface import implementer

from twisted.application import service
from twisted.application.service import IServiceMaker
from twisted.cred.checkers import ICredentialsChecker
from twisted.cred.credentials import IUsernamePassword
from twisted.cred.error import UnauthorizedLogin
from twisted.cred.portal import IRealm, Portal
from twisted.internet import defer, endpoints
from twisted.plugin import IPlugin
from twisted.python import usage
from twisted.web import resource, server, static
from twisted.web.guard import BasicCredentialFactory, HTTPAuthSessionWrapper
from twisted.web.resource import IResource

os.environ["DJANGO_SETTINGS_MODULE"] = "main.settings"


class Options(usage.Options):
    optFlags = []

    optParameters = [
        ["config", "c", "config.toml", "Path to config file",],
    ]


class Root(resource.Resource):
    def __init__(self, asgi_resource, index_file_resource):
        resource.Resource.__init__(self)
        self.asgi_resource = asgi_resource
        self.index_file_resource = index_file_resource

    def getChild(self, path, request):
        if path == b"":
            return self.index_file_resource
        path0 = request.prepath.pop(0)
        request.postpath.insert(0, path0)
        return self.asgi_resource


class ASGIService(service.Service):
    def __init__(self, site, resource, description):
        self.site = site
        self.resource = resource
        self.description = description

    def startService(self):
        self.endpoint = endpoints.serverFromString(reactor, self.description)
        self.endpoint.listen(self.site)

    def stopService(self):
        self.resource.stop()


class SchedulerService(service.Service):
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def startService(self):
        self.scheduler.start()

    def stopService(self):
        self.scheduler.shutdown()


class UpdateTorrentDatabase:
    def __init__(self, partial_update_delay, full_update_delay):
        self.last_partial = 0
        self.last_full = 0
        self.partial_update_delay = partial_update_delay
        self.full_update_delay = full_update_delay
        self.lock = threading.Lock()

    def cycle(self):
        from spreadsheetui.tasks import update_torrents

        if not self.lock.acquire(blocking=False):
            return
        try:
            if self.last_full + self.full_update_delay < time.monotonic():
                logger.info("Running a full update")
                update_torrents(partial_update=False)
                self.last_partial, self.last_full = time.monotonic(), time.monotonic()
            elif self.last_partial + self.partial_update_delay < time.monotonic():
                logger.info("Running a partial update")
                update_torrents(partial_update=True)
                self.last_partial = time.monotonic()
        finally:
            self.lock.release()


class File(static.File):
    def directoryListing(self):
        return self.forbidden


@implementer(IRealm)
class SpreadsheetRealm:
    def __init__(self, resource):
        self._resource = resource

    def requestAvatar(self, avatarId, mind, *interfaces):
        if IResource in interfaces:
            return (IResource, self._resource, lambda: None)
        raise NotImplementedError()


@implementer(ICredentialsChecker)
class PasswordDictCredentialChecker:
    credentialInterfaces = (IUsernamePassword,)

    def __init__(self, passwords):
        self.passwords = passwords

    def requestAvatarId(self, credentials):
        matched = self.passwords.get(credentials.username, None)
        if matched and matched == credentials.password:
            return defer.succeed(credentials.username)
        else:
            return defer.fail(UnauthorizedLogin("Invalid username or password"))


def wrap_with_auth(resource, passwords, realm="Auth"):
    """
    @param resource: resource to protect
    @param passwords: a dict-like object mapping usernames to passwords
    """
    portal = Portal(
        SpreadsheetRealm(resource), [PasswordDictCredentialChecker(passwords)]
    )
    credentialFactory = BasicCredentialFactory(realm)
    return HTTPAuthSessionWrapper(portal, [credentialFactory])


@implementer(IServiceMaker, IPlugin)
class ServiceMaker(object):
    tapname = "spreadsheetui"
    description = "Spreadsheet UI"
    options = Options

    def makeService(self, options):
        config = toml.load(options["config"])
        os.environ["DATABASE_URL"] = config["django"]["database_url"]
        os.environ["SECRET_KEY"] = config["django"]["secret_key"]
        logger.remove(0)
        logger.add(sys.stdout, level="INFO")

        multi = service.MultiService()

        scheduler_service = SchedulerService()
        multi.addService(scheduler_service)

        django.setup()
        application = get_default_application()
        from django.conf import settings

        from django.core import management

        management.call_command("migrate")
        management.call_command("collectstatic", "--no-input")
        from spreadsheetui.tasks import import_config

        import_config(options["config"])

        asgiresource = ASGIResource(
            application, automatic_proxy_header_handling=True, use_x_sendfile=True
        )
        root = Root(
            asgiresource,
            File(Path(settings.STATIC_ROOT) / "spreadsheetui" / "index.html"),
        )
        root.putChild(
            settings.STATIC_URL.strip("/").encode("utf-8"),
            File(settings.STATIC_ROOT.encode("utf-8")),
        )
        site = server.Site(
            wrap_with_auth(
                root,
                {
                    config["spreadsheetui"]["username"]
                    .encode("utf-8"): config["spreadsheetui"]["password"]
                    .encode("utf-8")
                },
            )
        )

        multi.addService(
            ASGIService(
                site, asgiresource, config["spreadsheetui"]["endpoint_description"]
            )
        )

        def twisted_started():
            def cleanup_thread():
                from django.db import close_old_connections

                close_old_connections()

            scheduler_service.scheduler.add_job(cleanup_thread, "interval", minutes=15)

            utd = UpdateTorrentDatabase(
                settings.TORRENT_UPDATE_PARTIAL_DELAY,
                settings.TORRENT_UPDATE_FULL_DELAY,
            )
            scheduler_service.scheduler.add_job(
                utd.cycle, "interval", seconds=2, max_instances=2
            )

        reactor.callLater(0, twisted_started)

        return multi


spreadsheetui = ServiceMaker()
