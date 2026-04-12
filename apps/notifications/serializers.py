from rest_framework import serializers

from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    comment_id = serializers.IntegerField(source="comment.id", read_only=True)
    comment_body = serializers.CharField(source="comment.body", read_only=True)
    post_slug = serializers.CharField(source="comment.post.slug", read_only=True)
    author = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = (
            "id",
            "comment_id",
            "comment_body",
            "post_slug",
            "author",
            "is_read",
            "created_at",
        )
    
    def get_author(self, obj):
        author = obj.comment.author
        return {
            "id": author.id,
            "email": author.email,
        }