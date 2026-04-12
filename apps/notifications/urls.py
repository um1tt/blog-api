from django.urls import path

from .views import (
    MarkNotificationsReadView, NotificationCountView, NotificationListView,
)

urlpatterns = [
    path("count/", NotificationCountView.as_view(), name="notifications-count"),
    path("", NotificationListView.as_view(), name="notifications-list"),
    path("read/", MarkNotificationsReadView.as_view(), name="notifications-read"),
]