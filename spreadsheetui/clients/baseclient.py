from abc import ABCMeta, abstractmethod


class BaseClient(metaclass=ABCMeta):
    @abstractmethod
    def list():
        """
        Return a list of `TorrentData`
        """

    @abstractmethod
    def list_active():
        """
        Return a list of `TorrentData` with active torrents
        """
