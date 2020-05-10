import json
from datetime import datetime

import pytz
import requests
from loguru import logger
from requests.exceptions import RequestException

from ..exceptions import FailedToUpdateException
from ..torrent import TorrentData, TorrentState
from .baseclient import BaseClient


class TransmissionClient(BaseClient):
    _session_id = ""

    def __init__(self, url):
        self.url = url

    def _call(self, method, **kwargs):
        logger.debug(f"Calling {method!r} args {kwargs!r}")
        return requests.post(
            self.url,
            data=json.dumps({"method": method, "arguments": kwargs}),
            headers={"X-Transmission-Session-Id": self._session_id},
        )

    def call(self, method, **kwargs):
        try:
            r = self._call(method, **kwargs)
        except RequestException:
            raise FailedToUpdateException()
        if r.status_code == 409:
            self._session_id = r.headers["X-Transmission-Session-Id"]
            r = self._call(method, **kwargs)

        if r.status_code != 200:
            raise FailedToUpdateException()

        r = r.json()
        logger.debug("Got transmission reply")
        if r["result"] != "success":
            raise FailedToUpdateException()

        return r["arguments"]

    def _fetch_list_result(self, only_active):
        result = []
        fields = [
            "hashString",
            "name",
            "sizeWhenDone",
            "status",
            "error",
            "percentDone",
            "uploadedEver",
            "addedDate",
            "trackers",
            "rateUpload",
            "rateDownload",
        ]
        if only_active:
            call_result = self.call("torrent-get", ids="recently-active", fields=fields)
        else:
            call_result = self.call("torrent-get", fields=fields)
        for torrent in call_result["torrents"]:
            if torrent["error"] > 0:
                state = TorrentState.ERROR
            elif torrent["status"] > 0:
                state = TorrentState.ACTIVE
            else:
                state = TorrentState.STOPPED

            if torrent["trackers"]:
                tracker = ".".join(
                    torrent["trackers"][0]["announce"].split("/")[2].rsplit(".", 2)[1:]
                )
            else:
                tracker = "None"

            result.append(
                TorrentData(
                    torrent["hashString"],
                    torrent["name"],
                    torrent["sizeWhenDone"],
                    state,
                    torrent["percentDone"] * 100,
                    torrent["uploadedEver"],
                    datetime.utcfromtimestamp(torrent["addedDate"]).astimezone(
                        pytz.UTC
                    ),
                    tracker,
                    torrent["rateUpload"],
                    torrent["rateDownload"],
                    "",
                )
            )
        return result

    def list(self):
        return self._fetch_list_result(False)

    def list_active(self):
        return self._fetch_list_result(True)
