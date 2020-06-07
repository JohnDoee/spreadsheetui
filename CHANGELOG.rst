================================
Changelog
================================


Version Unreleased ()
--------------------------------

* Added: Fake client for testing
* Added: Filtering on torrent client and status
* Added: Support for template change
* Added: Jobs and jobmanager

* Change: Turned top summary into a bottom summary for current result
* Change: Using better date for rtorrent timestamp
* Change: Moved torrent clients out of the project and into its own library
* Change: Moved docker to postgres
* Change: Removed torrent clients into libtc

* Bugfix: rtorrent completion date corrected
* Bugfix: Making sure ratio is updated


Version 1.0.1 (11-05-2020)
--------------------------------

* Change: Added database lock
* Change: Made partial updates only actually modified torrents
* Change: Made torrent client loops run independent of each other

* Bugfix: getting an updated rtorrent view

Version 1.0.0 (10-05-2020)
--------------------------------

* Initial release