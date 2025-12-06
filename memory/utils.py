# memory/utils.py
from django.utils import timezone
from datetime import timedelta
from .models import UserActivity, MemoryItem
from django.db import models

def track_user_activity(user, activity_type, target_file=None, context=None):
    """Kullanici aktivitelerini takip et"""
    UserActivity.objects.create(
        user=user,
        activity_type=activity_type,
        target_file=str(target_file) if target_file else None,
        context=context or {},
        timestamp=timezone.now()
    )

def get_behavioral_suggestions(user, query):
    """Kullanici davranislarina gore oneriler"""
    try:
        # Son aktivitelere bak
        recent_activities = UserActivity.objects.filter(
            user=user,
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).order_by('-timestamp')[:10]
        
        suggestions = []
        
        # Benzer aramalarý öner
        search_activities = [act for act in recent_activities if act.activity_type == 'search_query']
        for activity in search_activities[:3]:
            search_query = activity.context.get('query', '')
            if search_query and search_query != query:
                suggestions.append({
                    'type': 'previous_search',
                    'content': f"'{search_query}' aramasini tekrar deneyin",
                    'confidence': 0.6,
                    'reason': 'Gecmiste benzer arama yaptiniz'
                })
        
        # Sýk kullanýlan dosya türlerini öner
        file_type_stats = MemoryItem.objects.filter(user=user).values('file_type').annotate(
            count=models.Count('id'),
            total_access=models.Sum('access_count')
        ).order_by('-total_access')[:3]
        
        for stat in file_type_stats:
            if stat['count'] > 0:
                suggestions.append({
                    'type': 'file_type_suggestion',
                    'content': f"{stat['file_type']} dosyalarini goruntuleyin",
                    'confidence': 0.5,
                    'reason': f"Bu turde {stat['count']} dosyaniz var"
                })
        
        return suggestions
        
    except Exception as e:
        return []

def rank_results_with_context(semantic_results, behavioral_suggestions, user):
    """Sonuclari context'e gore sirala"""
    try:
        # Basit ranking - eriþim sýklýðý ve benzerlik skoruna göre
        for result in semantic_results:
            memory_item = result['memory_item']
            
            # Eriþim sýklýðý bonusu
            access_bonus = min(memory_item.access_count * 0.1, 0.3)
            
            # Zaman bonusu (son eriþilenler)
            time_since_access = (timezone.now() - memory_item.last_accessed).total_seconds()
            time_bonus = max(0, 1 - (time_since_access / (7 * 24 * 3600))) * 0.2  # 1 haftalýk pencere
            
            # Final skor
            result['final_score'] = result['similarity_score'] + access_bonus + time_bonus
        
        # Final skora göre sýrala
        return sorted(semantic_results, key=lambda x: x['final_score'], reverse=True)
        
    except Exception as e:
        return semantic_results

def analyze_user_context(user):
    """Kullanicinin mevcut contextini analiz et"""
    try:
        current_time = timezone.now()
        
        # Son aktiviteler
        recent_activities = UserActivity.objects.filter(
            user=user,
            timestamp__gte=current_time - timedelta(hours=1)
        )
        
        # Sýk kullanýlan dosya türleri
        popular_file_types = MemoryItem.objects.filter(
            user=user,
            access_count__gt=0
        ).values('file_type').annotate(
            total_access=models.Sum('access_count')
        ).order_by('-total_access')[:3]
        
        return {
            'time_of_day': current_time.hour,
            'day_of_week': current_time.weekday(),
            'is_weekend': current_time.weekday() >= 5,
            'recent_activity_count': recent_activities.count(),
            'recent_activity_types': list(recent_activities.values_list('activity_type', flat=True)),
            'popular_file_types': [item['file_type'] for item in popular_file_types],
            'active_hours': 9 <= current_time.hour <= 17  # Çalýþma saatleri
        }
    except Exception as e:
        return {
            'time_of_day': timezone.now().hour,
            'day_of_week': timezone.now().weekday(),
            'is_weekend': timezone.now().weekday() >= 5,
            'recent_activity_count': 0,
            'recent_activity_types': [],
            'popular_file_types': [],
            'active_hours': True
        }