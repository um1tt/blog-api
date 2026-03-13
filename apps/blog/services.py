import json

import redis
from django.conf import settings


def publish_comment_event(*, post_slug, author_id, body):
    client = redis.Redis.from_url(settings.BLOG_REDIS_URL)
    payload = {
        "post_slug": post_slug,
        "author_id": author_id,
        "body": body,
    }
    client.publish("comments", json.dumps(payload, ensure_ascii=False))
