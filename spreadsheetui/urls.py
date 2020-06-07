from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register("torrents", views.TorrentViewSet)
router.register("torrentclients", views.TorrentClientViewSet)
router.register("jobs", views.JobViewSet)
urlpatterns = router.urls
