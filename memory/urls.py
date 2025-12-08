# memory/urls.py
from django.urls import path
from . import views
# Eğer chat_views.py dosyan memory klasörünün içindeyse (views.py ile yan yana):
try:
    from . import chat_views
except ImportError:
    # Eğer chat_views ayrı bir dosya değil de views.py içindeyse bu satır hata vermesin diye:
    pass

urlpatterns = [
    # --- İstatistikler ---
    path('stats/', views.get_detailed_memory_stats, name='views.get_detailed_memory_stats'),
    path('stats/simple/', views.get_simple_memory_stats, name='views.get_simple_memory_stats'),
    path('stats/manager/', views.get_memory_stats_manager, name='views.get_memory_stats_manager'),
    
    # --- Timeline (Zaman Çizelgesi) ---
    path('timeline/manager/', views.get_fused_timeline_manager, name='views.get_fused_timeline_manager'),
    
    # HATA ÇIKARAN KISIM DÜZELTİLDİ:
    # views.py içinde 'get_timeline' yok, 'get_windows_recall_timeline' var. İsmi eşleştirdik.
    path('timeline/', views.get_windows_recall_timeline, name='get_timeline'),
    path('timeline/<str:date_str>/', views.get_timeline_by_date, name='memory-timeline-date'),

    # --- Diğer Endpointler ---
    path('suggestions/', views.get_memory_suggestions, name='memory-suggestions'),
    path('search/', views.search_memories, name='memory-search'),
    path('intelligent-search/', views.intelligent_search, name='intelligent-search'),
    path('activity/', views.track_user_activity, name='track-activity'),
    path('interact/', views.interact_with_ai, name='ai-interact'),

    # --- Chat Endpoint ---
    # Eğer chat_views.py varsa oradan, yoksa views içinden:
    path('chat/ask/', chat_views.chat_with_ai if 'chat_views' in locals() else views.interact_with_ai, name='chat_with_ai'),
]