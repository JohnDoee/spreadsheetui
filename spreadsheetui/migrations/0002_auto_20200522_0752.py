# Generated by Django 3.0.6 on 2020-05-22 07:52

import django.db.models.deletion
import jsonfield.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("spreadsheetui", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="torrentclient",
            name="client_type",
            field=models.CharField(
                choices=[
                    ("deluge", "Deluge"),
                    ("rtorrent", "rtorrent"),
                    ("transmission", "Transmission"),
                    ("fakeclient", "Fake Client"),
                ],
                max_length=30,
            ),
        ),
        migrations.CreateModel(
            name="Job",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "action",
                    models.CharField(
                        choices=[("start", "Start"), ("stop", "Stop")], max_length=20
                    ),
                ),
                ("config", jsonfield.fields.JSONField(blank=True, default={})),
                ("execute_start_time", models.DateTimeField(null=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "source_client",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="spreadsheetui.TorrentClient",
                    ),
                ),
                (
                    "target_client",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="spreadsheetui.TorrentClient",
                    ),
                ),
                (
                    "torrent",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="+",
                        to="spreadsheetui.Torrent",
                    ),
                ),
            ],
        ),
    ]
