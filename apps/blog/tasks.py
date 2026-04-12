import logging
from datetime import timedelta

from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone

from apps.blog.models import Comment, Post

logger = logging.getLogger(__name__)
User = get_user_model()

@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def invalidate_posts_cache_task():
    cache.delete("posts_list")
    cache.delete_pattern("posts_*") if hasattr(cache, "delete_pattern") else None

@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def generate_daily_stats():
    now = timezone.now()
    since = now - timedelta(hours=24)

    posts_count = Post.objects.filter(created_at__gte=since).count()
    comments_count = Comment.objects.filter(created_at__gte=since).count()
    users_count = User.objects.filter(date_joined__gte=since).count()

    logger.info(
        "Daily stats | posts=%s comments=%s users=%s",
        posts_count,
        comments_count,
        users_count,
    )
    return {
        "posts": posts_count,
        "comments": comments_count,
        "users": users_count,
    }