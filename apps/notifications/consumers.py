from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth.models import AnonymousUser

from apps.blog.models import Post

class CommentConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.slug = self.scope["url_route"]["kwargs"]["slug"]
        self.user = self.scope.get("user")
        if not self.user or isinstance(self.user, AnonymousUser) or not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        post_exists = await self._post_exists(self.sluf)
        if not post_exists:
            await self.close(code=4004)
            return 
        
        self.groups_name = f"post_comments_{self.slug}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        group_name = getattr(self, "group_name", None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)

    async def comment_created(self, event):
        await self.send_json(event["data"])

    @database_sync_to_async
    def _post_exists(self, slug):
        return Post.objects.filter(slug=slug).exists()