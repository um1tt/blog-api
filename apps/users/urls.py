from rest_framework.routers import DefaultRouter

from .views import RegisterViewSet

router = DefaultRouter()
router.register(r"auth/register", RegisterViewSet, basename="register")

urlpatterns = router.urls