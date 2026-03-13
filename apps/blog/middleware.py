from __future__ import annotations

from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone, translation
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import get_supported_language_variant

class UserLocaleMiddleware(MiddlewareMixin):
    def process_request(self, request):
        language = None

        if getattr(request, "user", None):
            language = getattr(request.user, "preferred_language", None)

        if not language:
            query_lang = request.GET.get("lang")
            if query_lang:
                try:
                    language = get_supported_language_variant(query_lang)
                except LookupError:
                    language = None

        if not language:
            language = settings.LANGUAGE_CODE
        translation.activate(language)
        request.LANGUAGE_CODE = language

        if getattr(request, "user", None) and request.user.is_authenticated:
            user_tz = getattr(request.user, "timezone", None)
            if user_tz:
                try:
                    timezone.activate(ZoneInfo(user_tz))
                except Exception:
                    timezone.deactivate()
            else: 
                timezone.deactivate()
        else:
            timezone.deactivate()

        