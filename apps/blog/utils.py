import json
import redis
from django.conf import settings

def publish_post_sse_event(post):
    redis_client = redis.Redis.from_url(settings.BLOG_REDIS_URL)

    payload = {
        "post_id": post.id,
        "title": post.title,
        "slug": post.slug,
        "author": {
            "id": post.author.id,
            "email": post.author.email,
        },
        "published_at": post.published_at.isoformat() if post.published_at else None,
    }

    redis_client.publish("posts_published", json.dumps(payload))