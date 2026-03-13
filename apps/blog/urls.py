from rest_framework.routers import DefaultRouter

from .views import CommentViewSet, PostViewSet, StatsViewSet

router = DefaultRouter()
router.register(r"posts", PostViewSet, basename="posts")
router.register(r"comments", CommentViewSet, basename="comments")
router.register(r"stats", StatsViewSet, basename="stats")

urlpatterns = router.urls
