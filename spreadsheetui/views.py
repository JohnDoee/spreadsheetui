from django.db.models import Count, Sum
from django_filters import rest_framework as filters
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Torrent


class TorrentSerializer(serializers.ModelSerializer):
    torrent_client = serializers.CharField(source="torrent_client.display_name")

    class Meta:
        model = Torrent
        fields = (
            "id",
            "infohash",
            "name",
            "torrent_client",
            "size",
            "state",
            "progress",
            "uploaded",
            "upload_rate",
            "download_rate",
            "tracker",
            "added",
            "ratio",
            "label",
        )


class TorrentFilter(filters.FilterSet):
    o = filters.OrderingFilter(
        fields=(
            ("id", "id"),
            ("name", "name"),
            ("uploaded", "uploaded"),
            ("ratio", "ratio"),
            ("size", "size"),
            ("upload_rate", "upload_rate"),
            ("download_rate", "download_rate"),
            ("added", "added"),
        ),
    )

    class Meta:
        model = Torrent
        fields = {"name": ["exact", "icontains"]}


class TorrentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Torrent.objects.all().prefetch_related("torrent_client")
    serializer_class = TorrentSerializer
    filterset_class = TorrentFilter

    @action(detail=False, methods=["get"])
    def stats(self, request):
        return Response(
            self.queryset.aggregate(
                total_torrents=Count("id"),
                total_size=Sum("size"),
                total_uploaded=Sum("uploaded"),
                total_upload_rate=Sum("upload_rate"),
                total_download_rate=Sum("download_rate"),
            )
        )
