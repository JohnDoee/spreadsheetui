from django.conf import settings
from django.db.models import Count, Sum
from django_filters import rest_framework as filters
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Torrent, TorrentClient, Job


class TorrentSerializer(serializers.ModelSerializer):
    torrent_client = serializers.CharField(source="torrent_client.display_name")
    torrent_client_id = serializers.IntegerField(source="torrent_client.id")

    class Meta:
        model = Torrent
        fields = (
            "id",
            "infohash",
            "name",
            "torrent_client",
            "torrent_client_id",
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


class CharInFilter(filters.BaseInFilter, filters.CharFilter):
    pass

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
    torrent_client__in = CharInFilter(field_name='torrent_client__name', lookup_expr='in')
    state__in = CharInFilter(field_name='state', lookup_expr='in')

    class Meta:
        model = Torrent
        fields = {"name": ["exact", "icontains"]}


class TorrentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Torrent.objects.filter(torrent_client__enabled=True).prefetch_related("torrent_client")
    serializer_class = TorrentSerializer
    filterset_class = TorrentFilter

    @action(detail=False, methods=["post"])
    def schedule_full_update(self, request):
        for updater in settings.TORRENT_CLIENT_UPDATERS:
            updater.schedule_full_update()
        return Response({'status': 'success', 'message': 'Full update scheduled'})

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

    @action(detail=False, methods=["get"])
    def aggregated(self, request):
        f = self.filterset_class(request.query_params, queryset=self.get_queryset())
        result = dict(f.qs.aggregate(
            name=Count("id"),
            size=Sum("size"),
            uploaded=Sum("uploaded"),
            upload_rate=Sum("upload_rate"),
            download_rate=Sum("download_rate"),
        ))
        return Response(result)


class TorrentClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = TorrentClient
        fields = ('id', 'name', 'display_name', )


class TorrentClientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TorrentClient.objects.filter(enabled=True)
    serializer_class = TorrentClientSerializer


class JobSerializer(serializers.ModelSerializer):
    torrent = serializers.CharField(source="torrent.name")
    source_client = serializers.CharField(source="torrent.torrent_client.display_name", allow_null=True)
    target_client = serializers.CharField(source="target_client.display_name", allow_null=True)

    class Meta:
        model = Job
        fields = ('id', "action", "torrent", "source_client", "target_client", "can_execute", "execute_start_time")


class AddJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ("action", "torrent", "target_client", "config")


class JobViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Job.objects.all().prefetch_related("target_client", "torrent", "torrent__torrent_client")
    serializer_class = JobSerializer

    @action(detail=False, methods=["POST"])
    def submit_actions(self, request):
        serializers = AddJobSerializer(data=request.data, many=True)
        serializers.is_valid(raise_exception=True)
        serializers.save()
        return Response({'status': 'success', 'message': 'Jobs queued'})

    @action(detail=False, methods=["POST"])
    def wipe_all_actions(self, request):
        Job.objects.all().delete()
        return Response({'status': 'success', 'message': 'All jobs wiped'})

    @action(detail=False, methods=["POST"])
    def execute_all_jobs(self, request):
        Job.objects.all().update(can_execute=True)
        if settings.SCHEDULER_SERVICE:
            settings.SCHEDULER_SERVICE.scheduler.add_job(settings.EXECUTE_JOBS_SERVICE.cycle, 'interval', id="execute_jobs_job", seconds=1)

        return Response({'status': 'success', 'message': 'All jobs queued for execution'})