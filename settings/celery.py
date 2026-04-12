import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.settings")

app = Celery("blog_api")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.broker_url = os.getenv("BLOG_CELERY_BROKER_URL", "redis://redis:6379/1")
app.conf.result_backend = os.getenv("BLOG_CELERY_BROKER_URL", "redis://redis:6379/1")

app.conf.beat_schedule = {
    "publish-scheduled-posts-every-minute": {
        "task": "apps.blog.tasks.publish_scheduled_posts",
        "schedule": crontab(minute="*"),
    },
    "clear-expired-notifications-daily": {
        "task": "apps.notifications.tasks.clear_expired_notifications",
        "schedule": crontab(hour=3, minute=0),
    },
    "generate-daily-stats-midnight": {
        "task": "apps.blog.tasks.generate_daily_stats",
        "schedule": crontab(hour=0, minute=0),
    },
}