import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from notifications.routing import websocket_urlpatterns
import groups.routing  # WebSocket route'larýnýzý burada import edin

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cloud_mvp.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            groups.routing.websocket_urlpatterns  # WebSocket URL'leriniz
        )
    ),
})