from __future__ import annotations
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from apps.users.tasks import send_welcome_email

import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _, override
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger("users")

from .models import User

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
    
    def create(self, validated_data):
        logger.info("Registration attempt for email: %s", validated_data.get("email"))
        validated_data.pop("password2", None)
        password = validated_data.pop("password")

        user = User.objects.create_user(password=password, **validated_data)
        send_welcome_email.delay(user.email)
        logger.info("User registered: %s", user.email)
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