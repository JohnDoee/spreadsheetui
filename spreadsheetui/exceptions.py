class SpreadsheetUiException(Exception):
    """Base exception"""


class FailedToUpdateException(SpreadsheetUiException):
    """Failed to update torrent client"""
