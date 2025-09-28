import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
import notifications.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cloud_mvp.settings")
django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # "websocket": AuthMiddlewareStack(  # Bu kýsmý geçici olarak kapat
    #     URLRouter(
    #         routing.websocket_urlpatterns
    #     )
    # ),
    })