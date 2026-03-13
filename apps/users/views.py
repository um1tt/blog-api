from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .serializers import (
    LanguageUpdateSerializer, 
    RegisterSerializer,
    TimezoneUpdateSerializer,
)

class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        summary="Register a new user",
        description=(
            "Creates a new user account, stored preferred language and timezone, "
            "returns JWT tokens, and sends a welcome email rendered from templates "
            "in the language selected at registration."
        ),
        request=RegisterSerializer,
        responses={
            201: RegisterSerializer,
            400: OpenApiResponse(description="Validation Error"),
            429: OpenApiResponse(description="Too many requests"),
        },
        examples=[
            OpenApiExample(
                "Register request",
                request_only=True,
                value={
                    "email": "aibek@example.com",
                    "first_name": "Aibek",
                    "last_name": "Mannapov",
                    "preferred_language": "ru",
                    "timezone": "Asia/Almaty",
                    "password": "12345678",
                    "password2": "12345678",
                },
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @extend_schema(
        tags=["Auth"],
        summary="Update preferred language",
        description=(
            "Updates the authenticated user's preferred language. "
            "Supported values are en, ru, and kk."
        ),
        request = LanguageUpdateSerializer,
        responses={
            200:OpenApiResponse(description="Language updated"),
            400:OpenApiResponse(description="Validation error"),
            401:OpenApiResponse(description="Unauthorized"),
            },
        examples=[
            OpenApiExample(
                "Language request",
                request_only=True,
                value={"preferred_language": "kk"},
            ),
            OpenApiExample(
                "Language response",
                response_only=True,
                value={"detail": "Language updated successfully."},
            ),
        ],
    )
    @action(
        detail=False,
        methods=["patch"],
        permission_classes=[IsAuthenticated],
        url_path="language",
    )
    def language(self, request):
        serializer = LanguageUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request.user.preferred_language = serializer.validated_data["preferred_language"]
        request.user.save(update_fields=["preferred_language"])

        return Response({"detail": _("Language updated successfully.")})
    
    @extend_schema(
        tags=["Auth"],
        summary="Update timezone",
        description=(
            "Updates the authenticated user's timezone. "
            "The value must be a valid IANA timezone identifier."
        ),
        request=TimezoneUpdateSerializer,
        responses={
            200:OpenApiResponse(description="Timezone updated"),
            400:OpenApiResponse(description="Validation error"),
            401:OpenApiResponse(description="Unauthorized"),
        },
        examples=[
            OpenApiExample(
                "Timezone request",
                request_only=True,
                value={"timezone": "Asia/Almaty"},
            ),
            OpenApiExample(
                "Timezone response",
                response_only=True,
                value={"detail": "Timezone updated successfully."},
            ),
        ],
    )
    @action(
        detail=False,
        methods=["patch"],
        permission_classes=[IsAuthenticated],
        url_path="timezone",
    )
    def timezone(self, request):
        serializer = TimezoneUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request.user.timezone = serializer.validated_data["timezone"]
        request.user.save(update_fields=["timezone"])
        return Response({"detail": _("Timezone updated successfully.")})