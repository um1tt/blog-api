from __future__ import annotations

import logging

from django.contrib.auth import get_user_model
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
        return user