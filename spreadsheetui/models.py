from django.db import models
from jsonfield import JSONField

from libtc import TORRENT_CLIENT_MAPPING, move_torrent


class TorrentClient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)

    client_type = models.CharField(
        max_length=30,
        choices=(
            (c.identifier, c.display_name) for c in TORRENT_CLIENT_MAPPING.values()
        ),
    )
    config = JSONField()
    enabled = models.BooleanField(default=True)

    def get_client(self):
        client_cls = TORRENT_CLIENT_MAPPING[self.client_type]
        return client_cls(**self.config)

    def __repr__(self):
        return f"TorrentClient(name={self.name!r}, client_type={self.client_type!r}, enabled={self.enabled!r})"


class Torrent(models.Model):
    torrent_client = models.ForeignKey(TorrentClient, on_delete=models.CASCADE)
    infohash = models.CharField(max_length=40)
    name = models.CharField(max_length=1000)
    size = models.BigIntegerField(db_index=True)
    state = models.CharField(max_length=20, db_index=True)
    progress = models.DecimalField(max_digits=5, decimal_places=2)
    uploaded = models.BigIntegerField(db_index=True)
    tracker = models.CharField(max_length=200, db_index=True)
    added = models.DateTimeField(db_index=True)
    upload_rate = models.BigIntegerField(db_index=True)
    download_rate = models.BigIntegerField(db_index=True)
    label = models.CharField(max_length=1000, default="", blank=True)
    ratio = models.DecimalField(max_digits=8, decimal_places=3, default=0.0)

    class Meta:
        unique_together = (("torrent_client", "infohash"),)


class Job(models.Model):
    ACTION_START = 'start'
    ACTION_STOP = 'stop'
    ACTION_REMOVE = 'remove'
    ACTION_MOVE = 'move'
    action = models.CharField(max_length=20, choices=(
        (ACTION_START, 'Start'),
        (ACTION_STOP, 'Stop'),
        (ACTION_REMOVE, 'Remove'),
        (ACTION_MOVE, 'Move'),
    ))
    torrent = models.ForeignKey(Torrent, on_delete=models.CASCADE, null=True, related_name='+')
    target_client = models.ForeignKey(TorrentClient, on_delete=models.CASCADE, null=True, related_name='+')
    config = JSONField(default={}, blank=True)

    can_execute = models.BooleanField(default=False)
    execute_start_time = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True)

    def execute(self):
        if self.torrent.torrent_client == self.target_client:
            return

        if self.action == self.ACTION_START:
            client = self.torrent.torrent_client.get_client()
            client.start(self.torrent.infohash)
        elif self.action == self.ACTION_STOP:
            client = self.torrent.torrent_client.get_client()
            client.stop(self.torrent.infohash)
        elif self.action == self.ACTION_REMOVE:
            client = self.torrent.torrent_client.get_client()
            client.remove(self.torrent.infohash)
        elif self.action == self.ACTION_MOVE:
            client = self.torrent.torrent_client.get_client()
            target_client = self.target_client.get_client()
            fast_resume = self.torrent.progress == 100.0
            move_torrent(self.torrent.infohash, client, target_client, fast_resume=fast_resume)
