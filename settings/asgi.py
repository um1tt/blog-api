import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from apps.notifications.middleware import JWTQueryStringAuthMiddleware

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.settings")

django_asgi_app = get_asgi_application()

import apps.notifications.routing

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTQueryStringAuthMiddleware(
            URLRouter(
                apps.notifications.routing.websocket_urlpatterns
            )
        ),
    }
)