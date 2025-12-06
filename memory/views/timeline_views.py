# memory/views/timeline_views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta
from memory.services.advanced_memory_manager import AdvancedMemoryManager

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_timeline(request):
    """Windows Recall benzeri timeline görünümü"""
    try:
        days = int(request.GET.get('days', 7))
        limit = int(request.GET.get('limit', 50))
        
        memory_manager = AdvancedMemoryManager(request.user)
        timeline_events = memory_manager.get_timeline_events(days=days, limit=limit)
        
        return Response({
            'timeline_events': timeline_events,
            'period_days': days,
            'total_events': len(timeline_events)
        })
        
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_timeline_by_date(request, date_str):
    """Belirli bir tarih için timeline getir"""
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        start_datetime = timezone.make_aware(datetime.combine(target_date, datetime.min.time()))
        end_datetime = start_datetime + timedelta(days=1)
        
        from memory.models import MemoryItem, UserActivity
        
        # Ýlgili tarihteki memory item'larý
        memories = MemoryItem.objects.filter(
            user=request.user,
            created_at__gte=start_datetime,
            created_at__lt=end_datetime
        ).select_related('memory_tier')
        
        # Ýlgili tarihteki aktiviteler
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
        
        # Saate göre sýrala
        events.sort(key=lambda x: x['timestamp'])
        
        return Response({
            'date': date_str,
            'events': events,
            'total_events': len(events)
        })
        
    except Exception as e:
        return Response({"error": str(e)}, status=500)
