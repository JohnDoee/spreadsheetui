import random
import string

from datetime import datetime

import pytz

from ..torrent import TorrentData, TorrentState
from .baseclient import BaseClient

TORRENTS = []

def randomString(rng, letters, stringLength):
    return ''.join(rng.choice(letters) for i in range(stringLength))

def generate_torrent(rng):
    size = rng.randint(100000, 7000000000)
    return TorrentData(
        randomString(rng, 'abcdef0123456789', 40),
        randomString(rng, string.ascii_lowercase + ' ' + '0123456789', rng.randint(10, 26)),
        size,
        TorrentState.ACTIVE,
        100,
        rng.randint(size // 10, size * 20),
        datetime.utcfromtimestamp(rng.randint(1500000000, 1590000000)).astimezone(pytz.UTC),
        "example.com",
        rng.randint(0, 500) == 0 and rng.randint(100, 1000000),
        0,
        '',
    )

def touch_torrents(rng, torrents):
    for t in torrents:
        if t.upload_rate > 0:
            t.upload_rate = rng.randint(100, 1000000)
            t.uploaded += t.upload_rate * 10


class FakeClient(BaseClient):
    def __init__(self, seed, num_torrents):
        self.rng = random.Random(seed)
        TORRENTS.extend([generate_torrent(self.rng) for _ in range(num_torrents)])

    def list(self):
        touch_torrents(self.rng, TORRENTS)
        return TORRENTS

    def list_active(self):
        touch_torrents(self.rng, TORRENTS)
        return [t for t in TORRENTS if t.upload_rate > 0]
