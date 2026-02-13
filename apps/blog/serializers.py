from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Category, Comment, Post, Tag

User = get_user_model()

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")

class CommentSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source="author.email", read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "author_email", "body", "created_at")
        read_only_fields = ("id", "created_at", "author_email")

class PostListSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source="author.email", read_only=True)
    category = CategorySerializer(read_only=True, allow_null=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = (
            "id",
            "author_email",
            "title",
            "slug",
            "category",
            "tags",
            "status",
            "created_at",
            "updated_at",
        )

class PostCreateUpdateSerializer(serializers.ModelSerializer):
    category_slug = serializers.SlugField(write_only=True, required=False, allow_null=True)
    tag_slugs = serializers.ListField(child=serializers.SlugField(), write_only=True, required=False)

    class Meta:
        model = Post
        fields = ("title", "slug", "body", "status", "category_slug", "tag_slugs")

    def create(self, validated_data):
        category_slug = validated_data.pop("category_slug", None)
        tag_slugs = validated_data.pop("tag_slugs", [])

        request = self.context["request"]
        post = Post.objects.create(author=request.user, **validated_data)

        if category_slug: 
            post.category = Category.objects.filter(slug=category_slug).first()
            post.save(update_fields=["category"])

        if tag_slugs:
            tags = list(Tag.objects.filter(slug__in=tag_slugs))
            post.tags.set(tags)

        return post
    
    def update(self, instance, validated_data):
        category_slug = validated_data.pop("category_slug", None)
        tag_slugs = validated_data.pop("tag_slugs", None)

        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()

        if category_slug is not None:
            instance.category = Category.objects.filter(slug=category_slug).first()
            instance.save(update_fields=["category"])

            if tag_slugs is not None:
                tags = list(Tag.objects.filter(slug__in=tag_slugs))
                instance.tags.set(tags)

                return instance