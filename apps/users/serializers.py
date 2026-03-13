from __future__ import annotations
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import logging

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _, override
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger("users")

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    tokens = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "first_name", "last_name", "avatar", "password", "password2", "tokens")

    def get_tokens(self, obj):
        refresh = RefreshToken.for_user(obj)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}
    
    def validate_preferred_language(self, value):
        supported = {code for code, _ in User.LanguageChoices.choices}
        if value not in supported:
            raise serializers.ValidationError(_("Unsupported language."))
        return value

    def validate_timezone(self, value):
        try: 
            ZoneInfo(value)
        except ZoneInfoNotFoundError:
            raise serializers.ValidationError(_("Invalid IANA timezone identifier."))
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs
    
    def create(self, validate_data): 
        logger.info("Registration attempt for email: %s", validate_data.get("email"))
        validate_data.pop("password2", None)
        password = validate_data.pop("password")

        user = User.objects.create_user(password=password, **validate_data)
        logger.info("User registered: %s", user.email)
        with override(user.preferred_language):
            subject = render_to_string(
                "emails/welcome/subject.txt",
                {"user": user},
            ).strip()
            body = render_to_string(
                "emails/welcome.body.txt",
                {"user": user},
            )
            send_mail (
                subject=subject,
                message=body,
                from_email=None,
                recipient_list=[user.email],
                fail_silently=False,
            )

        return user
    
class LanguageUpdateSerializer(serializers.Serializer):
    preferred_language = serializers.ChoiceField(
        choices=User.LanguageChoices.choices,
        error_messages={
            "invalid_choice": _("Unsupported language."),
        },
    )

class TimezoneUpdateSerializer(serializers.Serializer):
    timezone = serializers.CharField()

    def validate_timezone(self, value):
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError:
            raise serializers.ValidationError(_("Invalid IANA timezone identifier,"))
        return value