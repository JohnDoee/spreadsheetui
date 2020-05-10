from datetime import datetime

import pytz
from deluge_client import DelugeRPCClient
from deluge_client.client import DelugeClientException

from ..exceptions import FailedToUpdateException
from ..torrent import TorrentData, TorrentState
from .baseclient import BaseClient


class DelugeClient(BaseClient):
    keys = [
        "name",
        "progress",
        "download_location",
        "state",
        "total_size",
        "time_added",
        "total_uploaded",
        "tracker_host",
        "upload_payload_rate",
        "download_payload_rate",
        "label",
    ]

    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    @property
    def client(self):
        return DelugeRPCClient(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            decode_utf8=True,
        )

    def _fetch_list_result(self, filter):
        result = []
        client = self.client
        try:
            with client:
                torrents = client.core.get_torrents_status(filter, self.keys)
        except (DelugeClientException, ConnectionError):
            raise FailedToUpdateException()
        for infohash, torrent_data in torrents.items():
            if torrent_data["state"] in ["Seeding", "Downloading"]:
                state = TorrentState.ACTIVE
            elif torrent_data["state"] in ["Error"]:
                state = TorrentState.ERROR
            else:
                state = TorrentState.STOPPED

            result.append(
                TorrentData(
                    infohash,
                    torrent_data["name"],
                    torrent_data["total_size"],
                    state,
                    torrent_data["progress"],
                    torrent_data["total_uploaded"],
                    datetime.utcfromtimestamp(torrent_data["time_added"]).astimezone(
                        pytz.UTC
                    ),
                    torrent_data["tracker_host"],
                    torrent_data["upload_payload_rate"],
                    torrent_data["download_payload_rate"],
                    torrent_data.get("label", ""),
                )
            )
        return result

    def list(self):
        return self._fetch_list_result({})

    def list_active(self):
        return self._fetch_list_result({"state": "Active"})
