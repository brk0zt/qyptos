# memory/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Memory stats
    path('stats/', views.get_detailed_memory_stats, name='views.get_detailed_memory_stats'),
    path('stats/simple/', views.get_simple_memory_stats, name='views.get_simple_memory_stats'),
    path('stats/manager/', views.get_memory_stats_manager, name='views.get_memory_stats_manager'),
    path('timeline/manager/', views.get_fused_timeline_manager, name='views.get_fused_timeline_manager'),

    # Timeline endpoints
    path('timeline/', views.get_windows_recall_timeline, name='views.get_windows_recall_timeline'),
    path('timeline/<str:date_str>/', views.get_timeline_by_date, name='memory-timeline-date'),

    
    # Diðer memory endpoints
    path('suggestions/', views.get_memory_suggestions, name='memory-suggestions'),
    path('search/', views.search_memories, name='memory-search'),
    path('intelligent-search/', views.intelligent_search, name='intelligent-search'),
    path('activity/', views.track_user_activity, name='track-activity'),
]
