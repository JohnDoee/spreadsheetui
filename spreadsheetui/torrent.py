class TorrentData:
    def __init__(
        self,
        infohash,
        name,
        size,
        state,
        progress,
        uploaded,
        added,
        tracker,
        upload_rate,
        download_rate,
        label,
    ):
        self.infohash = infohash
        self.name = name
        self.size = size
        self.state = state
        self.progress = progress
        self.uploaded = uploaded
        self.added = added
        self.tracker = tracker
        self.upload_rate = upload_rate
        self.download_rate = download_rate
        self.label = label

    def __repr__(self):
        return f"TorrentData(infohash={self.infohash!r}, name={self.name!r})"


class TorrentState:
    ACTIVE = "active"
    STOPPED = "stopped"
    ERROR = "error"
