from datetime import timedelta

from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.utils import timezone

from .models import Notification

@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def process_new_comment(comment_id: int):
    from apps.blog.models import Comment

    comment = (
        Comment.objects
        .select_related("author", "post", "post__author")
        .get(id=comment_id)
    )

    post = comment.post
    post_author = post.author
    
    if comment.author_id != post_author.id:
        Notification.objects.create(
            recipient=post_author,
            comment=comment,
        )
    payload = {
        "comment_id": comment_id,
        "author": {
            "id": comment.author.id,
            "email": comment.author.email,
        },
        "body": comment.body,
        "created_at": comment.created_at.isoformat(),
    }

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"post_comments_{post.slug}",
        {
            "type": "comment_created",
            "data": payload,
        },
    )

    return payload

@shared_task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def clear_expired_notifications():
    threshold = timezone.now() - timedelta(days=30)
    deleted_count, _ = Notification.objects.filter(created_at__lt=threshold).delete()
    return deleted_count