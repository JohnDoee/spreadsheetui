from datetime import datetime
from urllib.parse import urlsplit
from xmlrpc.client import Error as XMLRPCError
from xmlrpc.client import ServerProxy

import pytz
from loguru import logger

from ..exceptions import FailedToUpdateException
from ..scgitransport import SCGITransport
from ..torrent import TorrentData, TorrentState
from .baseclient import BaseClient


def create_proxy(url):
    parsed = urlsplit(url)
    proto = url.split(":")[0].lower()
    if proto == "scgi":
        if parsed.netloc:
            url = f"http://{parsed.netloc}"
            logger.debug(f"Creating SCGI XMLRPC Proxy with url {url}")
            return ServerProxy(url, transport=SCGITransport())
        else:
            path = parsed.path
            logger.debug(f"Creating SCGI XMLRPC Socket Proxy with socket file {path}")
            return ServerProxy("http://1", transport=SCGITransport(socket_path=path))
    else:
        logger.debug(f"Creating Normal XMLRPC Proxy with url {url}")
        return ServerProxy(url)


class RTorrentClient(BaseClient):
    def __init__(self, url):
        self.proxy = create_proxy(url)

    def _fetch_list_result(self, view):
        result = []
        try:
            torrents = self.proxy.d.multicall2(
                "",
                view,
                "d.get_hash=",
                "d.get_name=",
                "d.is_active=",
                "d.message=",
                "d.get_directory=",
                "d.get_size_bytes=",
                "d.get_completed_bytes=",
                "d.up.total=",
                "d.up.rate=",
                "d.down.rate=",
                "d.load_date=",
                "t.multicall=,t.get_url=",
                "d.custom1=",
            )
        except (XMLRPCError, ConnectionError):
            raise FailedToUpdateException()
        for torrent in torrents:
            if torrent[3]:
                state = TorrentState.ERROR
            elif torrent[2] == 0:
                state = TorrentState.STOPPED
            else:
                state = TorrentState.ACTIVE

            progress = (torrent[6] / torrent[5]) * 100
            if torrent[11]:
                tracker = ".".join(torrent[11][0][0].split("/")[2].rsplit(".", 2)[1:])
            else:
                tracker = "None"

            result.append(
                TorrentData(
                    torrent[0].lower(),
                    torrent[1],
                    torrent[5],
                    state,
                    progress,
                    torrent[7],
                    datetime.utcfromtimestamp(torrent[10]).astimezone(pytz.UTC),
                    tracker,
                    torrent[8],
                    torrent[9],
                    torrent[12],
                )
            )

        return result

    def list(self):
        return self._fetch_list_result("main")

    def list_active(self):
        try:
            if "spreadsheet_active" not in self.proxy.view.list():
                self.proxy.view.add("", "spreadsheet_active")
                self.proxy.view.filter(
                    "", "spreadsheet_active", "or={d.up.rate=,d.down.rate=}"
                )
        except (XMLRPCError, ConnectionError):
            raise FailedToUpdateException()
        return self._fetch_list_result("spreadsheet_active")
