from django.http import JsonResponse
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework import generics


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

