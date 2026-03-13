from django.utils import formats, timezone, translation
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from .models import Category, Comment, Post, Tag


class CategorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ("id", "name", "slug")

    def get_name(self, obj):
        language = translation.get_language() or "en"
        return obj.get_localized_name(language)


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
        extra_kwargs = {
            "body": {
                "error_messages": {
                    "blank": _("Comment body cannot be empty."),
                }
            }
        }


class PostListSerializer(serializers.ModelSerializer):
    author_email = serializers.EmailField(source="author.email", read_only=True)
    category = CategorySerializer(read_only=True, allow_null=True)
    tags = TagSerializer(many=True, read_only=True)
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()

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

    def _format_dt(self, value):
        local_dt = timezone.localtime(value)
        return formats.date_format(local_dt, "DATETIME_FORMAT", use_l10n=True)

    def get_created_at(self, obj):
        return self._format_dt(obj.created_at)

    def get_updated_at(self, obj):
        return self._format_dt(obj.updated_at)


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    category_slug = serializers.SlugField(write_only=True, required=False, allow_null=True)
    tag_slugs = serializers.ListField(
        child=serializers.SlugField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Post
        fields = ("title", "slug", "body", "status", "category_slug", "tag_slugs")
        extra_kwargs = {
            "title": {
                "error_messages": {
                    "blank": _("Title cannot be empty."),
                }
            },
            "body": {
                "error_messages": {
                    "blank": _("Body cannot be empty."),
                }
            },
            "slug": {
                "error_messages": {
                    "blank": _("Slug cannot be empty."),
                }
            },
        }

    def validate_status(self, value):
        allowed = {choice[0] for choice in Post._meta.get_field("status").choices}
        if value not in allowed:
            raise serializers.ValidationError(_("Unsupported post status."))
        return value

    def create(self, validated_data):
        category_slug = validated_data.pop("category_slug", None)
        tag_slugs = validated_data.pop("tag_slugs", [])
        request = self.context["request"]

        post = Post.objects.create(author=request.user, **validated_data)

        if category_slug:
            post.category = Category.objects.filter(slug=category_slug).first()
            post.save(update_fields=["category"])

        if tag_slugs:
            tags = Tag.objects.filter(slug__in=tag_slugs)
            post.tags.set(tags)

        return post

    def update(self, instance, validated_data):
        category_slug = validated_data.pop("category_slug", None)
        tag_slugs = validated_data.pop("tag_slugs", None)

        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        if category_slug is not None:
            instance.category = Category.objects.filter(slug=category_slug).first()
            instance.save(update_fields=["category"])

        if tag_slugs is not None:
            tags = Tag.objects.filter(slug__in=tag_slugs)
            instance.tags.set(tags)

        return instance
