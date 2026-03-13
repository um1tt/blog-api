import asyncio
import json
from django.conf import settings
from django.core.management.base import BaseCommand
from redis.asyncio import Redis

class Command(BaseCommand):
    help = "Listen for comment events asynchronously"

    def handle(self, *args, **options):
        asyncio.run(self.listen())

    async def listen(self):
        client = Redis.from_url(settings.BLOG_REDIS_URL, decode_responses=True)
        pubsub = client.pubsub()
        await pubsub.subscribe("comments")

        self.stdout.write(self.style.SUCCESS("Listening on Redis channel: comments"))

        try:
            while True:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True,
                    timeout=1.0,
                )
                if message and message.get("data"):
                    payload = json.loads(message["data"])
                    self.stdout.write(
                        f"New comment event: "
                        f"post={payload['post_slug']} "
                        f"author_id={payload['author_id']} "
                        f"body={payload['body']} "
                    )
                await asyncio.sleep(0.1)
        finally:
            await pubsub.unsubscribe("comments")
            await pubsub.close()
            await client.aclose()
