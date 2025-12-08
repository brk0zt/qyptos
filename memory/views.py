# -*- coding: utf-8 -*-
# memory/views.py
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .services.advanced_memory_manager import AdvancedMemoryManager
from .utils import get_behavioral_suggestions, rank_results_with_context, analyze_user_context, track_user_activity
from .models import MemoryItem, UserActivity, UserMemoryProfile # Modeller import edildi
from django.db import models
import logging
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.serializers.json import DjangoJSONEncoder
from django.views.decorators.http import require_http_methods
import json
from django.contrib.auth.decorators import login_required
import os # file_name için os eklendi
from .services.interaction_service import InteractionService

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def interact_with_ai(request):
    """
    Kullanıcının Semantik AI ile sohbet etmesini sağlayan uç nokta.
    """
    try:
        user_message = request.data.get('message')
        context = request.data.get('context', {}) # Örn: Şu an açık olan dosya, resim yolu vb.

        if not user_message:
            return Response({"error": "Mesaj boş olamaz."}, status=400)

        # Interaction servisini başlat
        service = InteractionService(request.user)
        
        # Yanıtı al
        ai_response = service.process_message(user_message, context)

        return Response({
            "success": True,
            "data": ai_response
        })

    except Exception as e:
        logger.error(f"AI Interaction Error: {e}")
        return Response({"error": str(e)}, status=500)

class EnhancedJSONEncoder(DjangoJSONEncoder):
    """
    Tarih/saat ve diger Django tiplerini daha iyi isleyen ozel JSON Encoder.
    """
    def default(self, obj):
        if hasattr(obj, 'to_dict'): # MemoryItem/TimelineEvent modellerine to_dict() metodu eklendiğini varsayıyoruz.
            return obj.to_dict()
        return super().default(obj)

# ----------------------------------------------------------------------
# ZAMAN ÇİZELGESİ (TIMELINE) FONKSİYONLARI - İSİM ÇAKIŞMASI DÜZELTİLDİ
# ----------------------------------------------------------------------

@login_required
@require_http_methods(["GET"])
def get_fused_timeline_manager(request):
    """
    Kullanicinin zaman cizelgesi olaylarini (Timeline Events) AdvancedMemoryManager ile getirir.
    Parametreler: days (int, istege bagli), limit (int, istege bagli)
    """
    try:
        # Sorgu parametrelerini güvenli bir şekilde al
        days = int(request.GET.get('days', 7)) # Varsayılan: Son 7 gün
        limit = int(request.GET.get('limit', 100))
        
        if days <= 0 or limit <= 0:
             return JsonResponse({'error': 'Gecersiz "days" veya "limit" degeri.'}, status=400)

        # İş mantığını AdvancedMemoryManager'a devret
        manager = AdvancedMemoryManager(request.user)
        timeline_data = manager.get_fused_timeline(days=days, limit=limit)

        return JsonResponse({
            'success': True,
            'timeline': timeline_data
        }, encoder=EnhancedJSONEncoder)

    except Exception as e:
        # Beklenmedik hataları yakala ve 500 dön
        print(f"Timeline hatasi: {e}")
        return JsonResponse({'error': 'Zaman cizelgesi alinirken sunucu hatasi olustu.'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_windows_recall_timeline(request):
    """Windows Recall benzeri, dogrudan DB'den okuma yapan timeline gorunumu (get_timeline fonksiyonunun yerine)"""
    try:
        days = int(request.GET.get('days', 7))
        limit = int(request.GET.get('limit', 50))
        
        # Basit timeline implementasyonu
        start_date = timezone.now() - timedelta(days=days)
        
        events = []
        
        # Memory item'ları
        memories = MemoryItem.objects.filter(
            user=request.user,
            created_at__gte=start_date
        ).select_related('memory_tier')[:limit//2]
        
        for memory in memories:
            events.append({
                'type': 'memory',
                'timestamp': memory.created_at,
                'title': f"{memory.file_name}",
                'description': f"{memory.file_type} - {memory.memory_tier.name}",
                'thumbnail': memory.thumbnail_path,
                'metadata': {
                    'file_path': memory.file_path,
                    'memory_tier': memory.memory_tier.name,
                    'access_count': memory.access_count
                }
            })
        
        # User activities
        activities = UserActivity.objects.filter(
            user=request.user,
            timestamp__gte=start_date
        )[:limit//2]
        
        for activity in activities:
            events.append({
                'type': 'activity',
                'timestamp': activity.timestamp,
                'title': f"{activity.activity_type}",
                'description': activity.target_file or activity.application,
                'metadata': {
                    'activity_type': activity.activity_type,
                    'application': activity.application,
                    'window_title': activity.window_title
                }
            })
        
        # Tarihe göre sırala
        events.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return Response({
            'timeline_events': events[:limit],
            'period_days': days,
            'total_events': len(events)
        })
        
    except Exception as e:
        logger.error(f"Windows Recall Timeline hatasi: {str(e)}")
        return Response({"error": str(e)}, status=500)

# ----------------------------------------------------------------------
# HAFIZA İSTATİSTİKLERİ FONKSİYONLARI - İSİM ÇAKIŞMASI DÜZELTİLDİ
# ----------------------------------------------------------------------

@login_required
@require_http_methods(["GET"])
def get_memory_stats_manager(request):
    """
    Kullanicinin hafiza kullanim istatistiklerini AdvancedMemoryManager ile getirir.
    """
    try:
        manager = AdvancedMemoryManager(request.user)
        stats = manager.get_user_stats()

        return JsonResponse({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        print(f"Istatistik hatasi (Manager): {e}")
        return JsonResponse({'error': 'Istatistikler alinirken sunucu hatasi olustu.'}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_timeline_by_date(request, date_str):
    """Belirli bir tarih icin timeline getir"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_datetime = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
        end_datetime = start_datetime + timedelta(days=1)
        
        # Memory item'ları
        memories = MemoryItem.objects.filter(
            user=request.user,
            created_at__gte=start_datetime,
            created_at__lt=end_datetime
        ).select_related('memory_tier')
        
        # İlgili tarihteki aktiviteler
        activities = UserActivity.objects.filter(
            user=request.user,
            timestamp__gte=start_datetime,
            timestamp__lt=end_datetime
        )
        
        events = []
        
        for memory in memories:
            events.append({
                'type': 'memory',
                'id': memory.id,
                'timestamp': memory.created_at,
                'title': memory.file_name,
                'file_type': memory.file_type,
                'file_path': memory.file_path,
                'memory_tier': memory.memory_tier.name,
                'thumbnail': memory.thumbnail_path,
                'content_summary': memory.content_summary
            })
            
        for activity in activities:
            events.append({
                'type': 'activity',
                'id': activity.id,
                'timestamp': activity.timestamp,
                'activity_type': activity.activity_type,
                'application': activity.application,
                'window_title': activity.window_title,
                'target_file': activity.target_file
            })
        
        # Saate göre sırala
        events.sort(key=lambda x: x['timestamp'])
        
        return Response({
            'date': date_str,
            'events': events,
            'total_events': len(events)
        })
        
    except Exception as e:
        logger.error(f"Timeline by date hatasi: {str(e)}")
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_detailed_memory_stats(request):
    """Kullanicinin memory istatistiklerini getir (get_memory_stats fonksiyonunun yerine, byte hesabi yapan versiyon)"""
    try:
        logger.info(f"Memory stats istegi - Kullanici: {request.user.username}")
        
        # Debug bilgisi
        print(f"Kullanici: {request.user}, Authenticated: {request.user.is_authenticated}")
        
        # Toplam memory item sayısı
        total_items = MemoryItem.objects.filter(user=request.user).count()
        
        # Toplam aktivite sayısı
        total_activities = UserActivity.objects.filter(user=request.user).count()
        
        # Farklı dosya türü sayısı
        file_type_count = MemoryItem.objects.filter(user=request.user).values('file_type').distinct().count()
        
        # Gerçek memory kullanımı hesapla (MB cinsinden)
        total_size_bytes = MemoryItem.objects.filter(user=request.user).aggregate(
            total_size=models.Sum('original_size')
        )['total_size'] or 0
        
        used_memory = total_size_bytes / (1024 * 1024 * 1024)  # GB'ye çevir
        total_memory = 10  # GB
        
        # Memory profili
        memory_profile, created = UserMemoryProfile.objects.get_or_create(
            user=request.user,
            defaults={'learning_rate': 0.1, 'last_activity': timezone.now()}
        )
        
        stats = {
            'used_memory': round(used_memory, 2),
            'total_memory': total_memory,
            'memory_percentage': round((used_memory / total_memory) * 100, 1),
            'total_items': total_items,
            'total_activities': total_activities,
            'file_type_count': file_type_count,
            'learning_rate': memory_profile.learning_rate,
            'last_activity': memory_profile.last_activity.isoformat() if memory_profile.last_activity else None,
            'status': 'active',
            'total_size_mb': round(total_size_bytes / (1024 * 1024), 2)
        }
        
        logger.info(f"Detailed Memory stats basarili: {stats}")
        return Response(stats)
        
    except Exception as e:
        logger.error(f"Detailed Memory stats hatasi: {str(e)}")
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def track_user_activity(request):
    """Kullanici aktivitelerini takip et"""
    data = request.data
    activity_type = data.get('activity_type')
    target_file = data.get('target_file')
    context = data.get('context', {})
    
    # Aktiviteyi memory sistemine kaydet
    track_user_activity(
        user=request.user,
        activity_type=activity_type,
        target_file=target_file,
        context=context
    )
    
    return Response({"status": "tracked"})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_memory_suggestions(request):
    """Kullanici icin oneriler getir"""
    try:
        memory_manager = AdvancedMemoryManager(request.user)
        
        # Basit öneriler sistemi
        context = analyze_user_context(request.user)
        suggestions = memory_manager.get_contextual_suggestions(context)
        
        return Response(suggestions)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_memories(request):
    """Hafizada arama yap"""
    try:
        query = request.data.get('query')
        file_type = request.data.get('file_type')
        
        if not query:
            return Response({"error": "Arama sorgusu gerekli"}, status=400)
        
        memory_manager = AdvancedMemoryManager(request.user)
        results = memory_manager.semantic_search(query, file_type)
        
        return Response(results)
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def intelligent_search(request):
    """Akilli semantic arama"""
    try:
        query = request.data.get('query', '')
        file_type = request.data.get('file_type')
        limit = request.data.get('limit', 10)
        
        if not query:
            return Response({"error": "Arama sorgusu gerekli"}, status=400)
        
        memory_manager = AdvancedMemoryManager(request.user)
        
        # 1. Semantic arama
        semantic_results = memory_manager.semantic_search(query, file_type, limit)
        
        # 2. Behavioral öneriler (kullanıcı pattern'lerine göre)
        behavioral_suggestions = get_behavioral_suggestions(request.user, query)
        
        # 3. Context-aware ranking
        ranked_results = rank_results_with_context(
            semantic_results, 
            behavioral_suggestions,
            request.user
        )
        
        return Response({
            'query': query,
            'semantic_results': [
                {
                    'file_path': result['file_path'],
                    'file_type': result['file_type'],
                    'similarity_score': result['similarity_score'],
                    'last_accessed': result['memory_item'].last_accessed.isoformat() if hasattr(result['memory_item'].last_accessed, 'isoformat') else str(result['memory_item'].last_accessed),
                    'access_count': result['memory_item'].access_count
                }
                for result in ranked_results
            ],
            'behavioral_suggestions': behavioral_suggestions
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contextual_suggestions(request):
    """Kullanicinin mevcut context'ine gore oneriler"""
    try:
        # Context analizi (zaman, mevcut açık dosyalar, son aktiviteler)
        context = analyze_user_context(request.user)
        
        memory_manager = AdvancedMemoryManager(request.user)
        suggestions = memory_manager.get_contextual_suggestions(context)
        
        return Response({
            'context': context,
            'suggestions': suggestions
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_memory_stats(request):
    """Kullanici hafiza istatistiklerini getir (MemoryItem/UserActivity sayimi)"""
    try:
        
        memory_count = MemoryItem.objects.filter(user=request.user).count()
        activity_count = UserActivity.objects.filter(user=request.user).count()
        
        # Dosya türüne göre dağılım
        file_types = MemoryItem.objects.filter(user=request.user).values('file_type').annotate(count=models.Count('id'))
        
        return Response({
            'memory_items_count': memory_count,
            'activity_count': activity_count,
            'file_type_distribution': list(file_types),
            'memory_usage': 'active'  # Basit durum bilgisi
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_simple_memory_stats(request):
    """Kullanicinin memory istatistiklerini getir (get_memory_stats fonksiyonunun yerine, basit hesaplama yapan versiyon)"""
    try:
        
        # Toplam memory item sayısı
        total_items = MemoryItem.objects.filter(user=request.user).count()
        
        # Toplam aktivite sayısı
        total_activities = UserActivity.objects.filter(user=request.user).count()
        
        # Farklı dosya türü sayısı
        file_type_count = MemoryItem.objects.filter(user=request.user).values('file_type').distinct().count()
        
        # Kullanılan memory hesaplama (örnek: her item 0.1 GB)
        used_memory = total_items * 0.1
        total_memory = 10  # GB
        
        # Memory profili
        memory_profile, created = UserMemoryProfile.objects.get_or_create(
            user=request.user,
            defaults={'learning_rate': 0.1, 'last_activity': timezone.now()}
        )
        
        return Response({
            'used_memory': round(used_memory, 2),
            'total_memory': total_memory,
            'memory_percentage': round((used_memory / total_memory) * 100, 1),
            'total_items': total_items,
            'total_activities': total_activities,
            'file_type_count': file_type_count,
            'learning_rate': memory_profile.learning_rate,
            'last_activity': memory_profile.last_activity.isoformat() if memory_profile.last_activity else None,
            'status': 'active'
        })
        
    except Exception as e:
        return Response({"error": str(e)}, status=500)