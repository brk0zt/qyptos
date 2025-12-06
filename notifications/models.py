from django.conf import settings
from django.db import models

class Notification(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.CASCADE, related_name='app_notifications')  # ← Doğru
    text = models.TextField()
    target_url = models.CharField(max_length=255, blank=True, null=True) 
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_name='app_notifications'
    def __str__(self):
        return f"Notification for {self.user}"