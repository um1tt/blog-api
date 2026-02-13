from __future__ import annotations

import logging

from rest_framework import mixins, viewsets
from rest_framework.permissions import AllowAny

from .serializers import RegisterSerializer

logger = logging.getLogger("users")

class RegisterViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
