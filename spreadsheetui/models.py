from django.db import models
from jsonfield import JSONField

from .clients import DelugeClient, RTorrentClient, TransmissionClient


class TorrentClient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)

    CLIENT_TYPE_DELUGE = "deluge"
    CLIENT_TYPE_RTORRENT = "rtorrent"
    CLIENT_TYPE_TRANSMISSION = "transmission"
    client_type = models.CharField(
        max_length=30,
        choices=(
            (CLIENT_TYPE_DELUGE, "Deluge"),
            (CLIENT_TYPE_RTORRENT, "rtorrent"),
            (CLIENT_TYPE_TRANSMISSION, "Transmission"),
        ),
    )
    config = JSONField()
    enabled = models.BooleanField(default=True)

    def get_client(self):
        client_cls = TORRENT_CLIENT_MAPPING[self.client_type]
        return client_cls(**self.config)

    def __repr__(self):
        return f"TorrentClient(name={self.name!r}, client_type={self.client_type!r}, enabled={self.enabled!r})"


TORRENT_CLIENT_MAPPING = {
    TorrentClient.CLIENT_TYPE_DELUGE: DelugeClient,
    TorrentClient.CLIENT_TYPE_TRANSMISSION: TransmissionClient,
    TorrentClient.CLIENT_TYPE_RTORRENT: RTorrentClient,
}


class Torrent(models.Model):
    torrent_client = models.ForeignKey(TorrentClient, on_delete=models.CASCADE)
    infohash = models.CharField(max_length=40)
    name = models.CharField(max_length=1000)
    size = models.BigIntegerField()
    state = models.CharField(max_length=20)
    progress = models.DecimalField(max_digits=5, decimal_places=2)
    uploaded = models.BigIntegerField()
    tracker = models.CharField(max_length=200)
    added = models.DateTimeField()
    upload_rate = models.BigIntegerField()
    download_rate = models.BigIntegerField()
    label = models.CharField(max_length=1000, default="", blank=True)
    ratio = models.DecimalField(max_digits=8, decimal_places=3, default=0.0)

    class Meta:
        unique_together = (("torrent_client", "infohash"),)
