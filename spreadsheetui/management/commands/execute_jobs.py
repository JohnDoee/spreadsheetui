import time

from django.core.management.base import BaseCommand

from spreadsheetui.tasks import execute_jobs


class Command(BaseCommand):
    help = "Execute all available jobs"

    def add_arguments(self, parser):
        parser.add_argument("--loop", dest="loop", action="store_true")

    def handle(self, *args, **options):
        if options["loop"]:
            while True:
                self.stdout.write(self.style.SUCCESS("Executing jobs"))
                execute_jobs()
                time.sleep(5)
        else:
            execute_jobs()
