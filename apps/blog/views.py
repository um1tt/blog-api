from __future__ import annotations
from django.core.cache import cache

import logging

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Comment, Post, PostStatus
from .permissions import IsOwnerOrReadOnly
from .serializers import CommentSerializer, PostCreateUpdateSerializer, PostListSerializer

logger = logging.getLogger("blog")

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related("author", "category").prefetch_related("tags")
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action in ("list", "retrieve", "comments"):
            return [AllowAny()]
        if self.action in ("create", ):
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        
    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_authenticated:
            return qs.filter(status=PostStatus.PUBLISHED)
        if self.action in ("list", "retrieve", "comments"):
            return (qs.filter(status=PostStatus.PUBLISHED) | qs.filter(author=self.request.user)).distinct()
        
        return qs
    
    def perform_create(self, serializer):
        logger.info("Post create attempt by user_id=%s", self.request.user.id)
        serializer.save()

    def perform_update(self, serializer):
        logger.info("Post update attempt by user_id=%s slug=%s", self.request.user.id, self.kwargs.get("slug"))
        serializer.save()

    def perform_destroy(self, instance):
        logger.info("Post delete by user_id=%s slug=%s", self.request.user.id, instance.slug)
        instance.delete()
        
    def list(self, request, *args, **kwargs):
        cache_key = "posts_list"

        data = cache.get(cache_key)
        if data:
            return Response(data)

        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        cache.set(cache_key, serializer.data, timeout=60)
        return Response(serializer.data)
    

    @action(detail=True, methods=["get", "post"], url_path="comments")
    def comments(self, request, slug=None):
        post = get_object_or_404(Post, slug=slug)

        if request.method == "GET":
            if post.status != PostStatus.PUBLISHED and (not request.user.is_authenticated or post.author_id != request.user.id):
                return Response(status=status.HTTP_404_NOT_FOUND)
            qs = Comment.objects.filter(post=post).select_related("author").order_by("-created_at")
            return Response(CommentSerializer(qs, many=True).data)

        if not request.user.is_authenticated:
            return Response({"detail": "Authentication credentials were not provided."}, status=401)

        serializer = CommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = Comment.objects.create(post=post, author=request.user, body=serializer.validated_data["body"])
        logger.info("Comment created post=%s user_id=%s", post.slug, request.user.id)
        return Response(CommentSerializer(comment).data, status=201)
    
    class CommentViewSet(viewsets.ModelViewSet):
        queryset = Comment.objects.select_related("author", "post").all()
        serializer_class = CommentSerializer
        permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

        def get_queryset(self):
            qs = super().get_queryset()
            user = self.request.user
            if user.is_authenticated:
                return qs
            return qs.none()
        def get_permissions(self):
            if self.action in ("list", "retrieve"):
                return [AllowAny()]
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
    