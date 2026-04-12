import asyncio
import json
from apps.notifications.tasks import process_new_comment
from apps.blog.tasks import invalidate_posts_cache_task

import redis.asyncio as aioredis
from django.conf import settings
from django.http import StreamingHttpResponse
import httpx
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Comment, Post
from .serializers import (
    CommentSerializer,
    PostCreateUpdateSerializer,
    PostListSerializer,
)
from .services import publish_comment_event

User = get_user_model()


def invalidate_posts_cache():
    try:
        cache.delete_pattern("posts_list:*")
    except Exception:
        cache.clear()


@extend_schema_view(
    list=extend_schema(
        tags=["Posts"],
        summary="List posts",
        description=(
            "Returns blog posts. Anonymous users see only published posts. "
            "Authenticated users see published posts and their own posts. "
            "The response is cached in Redis per language."
        ),
        responses={200: PostListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Posts"],
        summary="Retrieve a post",
        description="Returns one post by slug.",
        responses={
            200: PostListSerializer,
            404: OpenApiResponse(description="Not found"),
        },
    ),
    create=extend_schema(
        tags=["Posts"],
        summary="Create a post",
        description="Creates a post and invalidates Redis cache for all languages.",
        request=PostCreateUpdateSerializer,
        responses={
            201: PostListSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Unauthorized"),
        },
    ),
    partial_update=extend_schema(
        tags=["Posts"],
        summary="Partially update a post",
        description="Updates a post and invalidates Redis cache for all languages.",
        request=PostCreateUpdateSerializer,
        responses={
            200: PostListSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not found"),
        },
    ),
    destroy=extend_schema(
        tags=["Posts"],
        summary="Delete a post",
        description="Deletes a post and invalidates Redis cache for all languages.",
        responses={
            204: OpenApiResponse(description="Deleted"),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not found"),
        },
    ),
)
class PostViewSet(viewsets.ModelViewSet):
    lookup_field = "slug"

    def get_queryset(self):
        queryset = Post.objects.select_related("author", "category").prefetch_related("tags")

        if self.request.user.is_authenticated:
            return queryset.filter(
                Q(status="published") | Q(author=self.request.user)
            ).distinct()

        return queryset.filter(status="published")

    def get_serializer_class(self):
        if self.action in ("create", "partial_update", "update"):
            return PostCreateUpdateSerializer
        return PostListSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [AllowAny()]
        if self.action == "comments" and self.request.method == "GET":
            return [AllowAny()]
        return [IsAuthenticated()]

    def list(self, request, *args, **kwargs):
        language = getattr(request, "LANGUAGE_CODE", "en")
        cache_key = f"posts_list:{language}"

        cached_data = cache.get(cache_key)
        if cached_data is not None:
            return Response(cached_data)

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        cache.set(cache_key, serializer.data, timeout=60)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        post = serializer.save()
        process_new_comment.delay(comment.id)
        invalidate_posts_cache_task.delay()
        response_serializer = PostListSerializer(post, context={"request": request})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        post = serializer.save()
        invalidate_posts_cache_task.delay()
        response_serializer = PostListSerializer(post, context={"request": request})
        return Response(response_serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        invalidate_posts_cache_task.delay()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Comments"],
        summary="List or create comments for a post",
        description=(
            "GET returns comments for the given post slug. "
            "POST creates a new comment and publishes a Redis event as JSON."
        ),
        request=CommentSerializer,
        responses={
            200: CommentSerializer(many=True),
            201: CommentSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not found"),
        },
        examples=[
            OpenApiExample(
                "Create comment request",
                request_only=True,
                value={"body": "Great post!"},
            ),
        ],
    )
    @action(detail=True, methods=["get", "post"], url_path="comments")
    def comments(self, request, slug=None):
        post = get_object_or_404(Post, slug=slug)

        if request.method == "GET":
            comments = post.comments.select_related("author").all()
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)

        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = Comment.objects.create(
            post=post,
            author=request.user,
            body=serializer.validated_data["body"],
        )

        publish_comment_event(
            post_slug=post.slug,
            author_id=request.user.id,
            body=comment.body,
        )

        response_serializer = CommentSerializer(comment)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    list=extend_schema(
        tags=["Comments"],
        summary="List comments",
        description="Returns all comments.",
        responses={200: CommentSerializer(many=True)},
    ),
    retrieve=extend_schema(
        tags=["Comments"],
        summary="Retrieve comment",
        description="Returns one comment by id.",
        responses={
            200: CommentSerializer,
            404: OpenApiResponse(description="Not found"),
        },
    ),
)
class CommentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Comment.objects.select_related("author", "post").all()
    serializer_class = CommentSerializer
    permission_classes = [AllowAny]


class StatsViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Stats"],
        summary="Get blog statistics with external data",
        description=(
            "Returns local blog statistics together with exchange rates and current Almaty time. "
            "This view is async because two external APIs are independent I/O operations. "
            "With asyncio.gather both requests are awaited concurrently instead of sequentially."
        ),
        responses={
            200: OpenApiResponse(description="Statistics response"),
        },
        examples=[
            OpenApiExample(
                "Stats response",
                response_only=True,
                value={
                    "blog": {
                        "total_posts": 42,
                        "total_comments": 137,
                        "total_users": 15,
                    },
                    "exchange_rates": {
                        "KZT": 450.23,
                        "RUB": 89.10,
                        "EUR": 0.92,
                    },
                    "current_time": "2024-03-15T18:30:00+05:00",
                },
            )
        ],
    )
    async def list(self, request):
        # Async is used because the endpoint performs multiple independent external HTTP requests.
        # If written synchronously, the second API call would wait for the first and total latency would be higher.
        async with httpx.AsyncClient(timeout=10.0) as client:
            rates_task = client.get("https://open.er-api.com/v6/latest/USD")
            time_task = client.get(
                "https://timeapi.io/api/time/current/zone?timeZone=Asia/Almaty"
            )
            rates_response, time_response = await asyncio.gather(rates_task, time_task)

        rates_response.raise_for_status()
        time_response.raise_for_status()

        rates_data = rates_response.json()
        time_data = time_response.json()

        total_posts, total_comments, total_users = await asyncio.gather(
            sync_to_async(Post.objects.count)(),
            sync_to_async(Comment.objects.count)(),
            sync_to_async(User.objects.count)(),
        )

        payload = {
            "blog": {
                "total_posts": total_posts,
                "total_comments": total_comments,
                "total_users": total_users,
            },
            "exchange_rates": {
                "KZT": rates_data["rates"]["KZT"],
                "RUB": rates_data["rates"]["RUB"],
                "EUR": rates_data["rates"]["EUR"],
            },
            "current_time": time_data["dateTime"],
        }
        return Response(payload)

async def post_stream_view(request):
    redis_client = aioredis.from_url(settings.BLOG_REDIS_URL, decode_responses=True)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("posts_published")

    async def event_stream():
        try: 
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message and message["type"] == "message":
                    yield f"data: {message['data']}\n\n"
                await asyncio.sleep(0.1)
        finally:
            await pubsub.unsubscribe("posts_published")
            await pubsub.close()
            await redis_client.close()

    response = StreamingHttpResponse(
        streaming_content=event_stream(),
        content_type="text/event-stream",
    )
    response["Cache-Control"] = "no-cache"
    return response