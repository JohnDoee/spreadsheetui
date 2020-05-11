import concurrent.futures
import time

import toml
from django.conf import settings
from django.db.models import Q
from loguru import logger

from .exceptions import FailedToUpdateException
from .models import Torrent, TorrentClient


def update_torrents(clients=None, partial_update=False):
    keys = [
        "name",
        "size",
        "state",
        "progress",
        "uploaded",
        "tracker",
        "added",
        "upload_rate",
        "download_rate",
        "label",
    ]
    torrent_clients = TorrentClient.objects.filter(enabled=True)
    if clients:
        torrent_clients = torrent_clients.filter(name__in=clients)

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        client_lists = {}
        for torrent_client in torrent_clients:
            client = torrent_client.get_client()
            if partial_update:
                method = client.list_active
            else:
                method = client.list
            client_lists[executor.submit(method)] = torrent_client

        for future in concurrent.futures.as_completed(client_lists):
            torrent_client = client_lists[future]
            try:
                torrent_datas = (
                    future.result()
                )  # TODO: handle exceptions this can throw
            except FailedToUpdateException:
                logger.warning(f"Failed to update {torrent_client}")
                continue
            existing_torrents = {
                t.infohash: t
                for t in Torrent.objects.filter(torrent_client=torrent_client)
            }
            seen_torrents = set()
            new_torrents = []
            update_torrents = []
            modified_torrent_fields = set()
            for torrent_data in torrent_datas:
                seen_torrents.add(torrent_data.infohash)
                if torrent_data.infohash in existing_torrents:
                    torrent = existing_torrents[torrent_data.infohash]
                    modified_torrent = False
                    for key in keys:
                        old_value = getattr(torrent, key)
                        new_value = getattr(torrent_data, key)
                        if old_value != new_value:
                            modified_torrent = True
                            modified_torrent_fields.add(key)
                            setattr(torrent, key, new_value)
                    if modified_torrent:
                        update_torrents.append(torrent)
                else:
                    torrent = Torrent(
                        torrent_client=torrent_client, infohash=torrent_data.infohash,
                    )
                    for key in keys:
                        setattr(torrent, key, getattr(torrent_data, key))
                    new_torrents.append(torrent)

                torrent.ratio = torrent.uploaded / torrent.size

            with settings.DATABASE_LOCK:
                if partial_update:
                    logger.debug(f"{torrent_client!r} Setting speeds to zero")
                    Torrent.objects.filter(torrent_client=torrent_client).filter(
                        Q(upload_rate__gt=0) | Q(download_rate__gt=0)
                    ).exclude(pk__in=[t.pk for t in update_torrents]).update(
                        upload_rate=0, download_rate=0
                    )

                logger.debug(f"{torrent_client!r} Creating {len(new_torrents)} torrents")
                Torrent.objects.bulk_create(new_torrents)

                if update_torrents:
                    logger.debug(f"{torrent_client!r} Updating {len(update_torrents)} torrents with fields {modified_torrent_fields!r}")
                    Torrent.objects.bulk_update(
                        update_torrents,
                        modified_torrent_fields,
                    )
                else:
                    logger.debug(f"{torrent_client!r} No torrents to update")

                if not partial_update:
                    to_delete = set(existing_torrents.keys()) - seen_torrents
                    logger.debug(f"{torrent_client!r} Deleting {len(to_delete)} torrents")
                    Torrent.objects.filter(
                        torrent_client=torrent_client, infohash__in=to_delete
                    ).delete()


def import_config(path):
    config = toml.load(path)
    seen_clients = []
    for name, config in config["clients"].items():
        seen_clients.append(name)
        display_name = config.pop("display_name", name)
        client_type = config.pop("client_type")
        TorrentClient.objects.update_or_create(
            name=name,
            defaults={
                "display_name": display_name,
                "client_type": client_type,
                "config": config,
                "enabled": True,
            },
        )

    TorrentClient.objects.exclude(name__in=seen_clients).update(enabled=False)


def loop_update_torrents():
    last_partial, last_full = 0, 0
    while True:
        if last_full + settings.TORRENT_UPDATE_FULL_DELAY < time.monotonic():
            logger.debug("Running a full update")
            update_torrents(partial_update=False)
            last_partial, last_full = time.monotonic(), time.monotonic()
        elif last_partial + settings.TORRENT_UPDATE_PARTIAL_DELAY < time.monotonic():
            logger.debug("Running a partial update")
            update_torrents(partial_update=True)
            last_partial = time.monotonic()
        time.sleep(1)
