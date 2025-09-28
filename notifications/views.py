from django.http import JsonResponse
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework import generics
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

class NotificationMarkAsReadView(generics.UpdateAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    
    def update(self, request, *args, **kwargs):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'success'})

def notification_list(request):
    notifications = Notification.objects.filter(user=request.user)
    # JSON response döndür veya template render et
    return JsonResponse({'notifications': list(notifications.values())})

def mark_as_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)

def mark_all_as_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})

@api_view(['GET'])
@permission_classes([AllowAny])
def notification_list(request):
    # Basit test verisi
    notifications = [
        {"id": 1, "message": "Hos geldiniz!", "read": False},
        {"id": 2, "message": "Sistem guncellendi", "read": True},
    ]
    return Response(notifications)

@api_view(['PATCH'])
@permission_classes([AllowAny])  # Geçici
def mark_all_as_read(request):
    return Response({"message": "Tum bildirimler okundu olarak isaretlendi"})

@api_view(['PATCH'])
@permission_classes([AllowAny])  # Geçici
def mark_as_read(request, notification_id):
    return Response({"message": f"{notification_id} numarali bildirim okundu"})