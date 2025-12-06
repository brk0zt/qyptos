from django.contrib import admin
from django.urls import path, include, re_path
from files.views import share_file_view, consume_file, download_file, secure_media_view
from django.conf import settings
from django.conf.urls.static import static
from chat.routing import websocket_urlpatterns
from memory.views import intelligent_search, get_contextual_suggestions

urlpatterns = [
    # test_view kaldýrýldý, share_file_view etkinleþtirildi
    re_path(r'^share/(?P<token>.+)/$', share_file_view, name='share-file'),
    path('api/secure-media/<uuid:token>/', secure_media_view, name='secure-media'),
    path('admin/', admin.site.urls),
    path('chat/', include('chat.urls')),
    path('api/consume/<int:file_id>/', consume_file, name='consume_file'),
    path('api/download/<int:file_id>/', download_file, name='download_file'),
    path('api/', include('files.urls')),
    path('api/', include('users.urls')),
    path('api/auth/', include('users.urls')),
    path('notifications/', include('notifications.urls')),
    path('ads/', include('ads.urls')),
    path('api/memory/', include('memory.urls')),  # Memory URLs eklenmiþ olmalý
    path('api/memory/search/', intelligent_search, name='intelligent_search'),
    path('api/memory/suggestions/', get_contextual_suggestions, name='context_suggestions'),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
