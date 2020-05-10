from django.core.management.base import BaseCommand

from spreadsheetui.tasks import import_config


class Command(BaseCommand):
    help = "Import a torrent config"

    def add_arguments(self, parser):
        parser.add_argument("config_path", type=str)

    def handle(self, *args, **options):
        import_config(options["config_path"])
        self.stdout.write(self.style.SUCCESS("Config imported"))
