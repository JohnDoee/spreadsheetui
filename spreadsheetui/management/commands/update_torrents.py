from django.core.management.base import BaseCommand

from spreadsheetui.tasks import loop_update_torrents, update_torrents


class Command(BaseCommand):
    help = "Update all active torrents"

    def add_arguments(self, parser):
        parser.add_argument("--loop", dest="loop", action="store_true")
        parser.add_argument("--partial", dest="partial", action="store_true")
        parser.add_argument("clients", nargs="*", type=str)

    def handle(self, *args, **options):
        if options["loop"]:
            self.stdout.write(self.style.SUCCESS("Starting loop"))
            loop_update_torrents()
        else:
            self.stdout.write(self.style.SUCCESS("Updating torrents"))
            update_torrents(options["clients"], options["partial"])
            self.stdout.write(self.style.SUCCESS("Torrents updated"))
