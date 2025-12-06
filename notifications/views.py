from django.http import JsonResponse
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework import generics
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Notification
from rest_framework.views import APIView

class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def get(self, request):
        notifs = Notification.objects.filter(user=request.user).order_by("-created_at")
        serializer = NotificationSerializer(notifs, many=True)
        return Response(serializer.data)

class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):
        try:
            notification = Notification.objects.get(id=notification_id, user=request.user)
            notification.is_read = True
            notification.save()
            return Response({"message": "Bildirim okundu olarak isaretlendi"})
        except Notification.DoesNotExist:
            return Response({"error": "Bildirim bulunamadi"}, status=404)

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