from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class UserStatus(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='status'
    )
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} ({'online' if self.is_online else 'offline'})"

class ChatThread(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="thread_user1")
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name="thread_user2")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user1", "user2")

    def __str__(self):
        return f"{self.user1.username} ? {self.user2.username}"

class Message(models.Model):
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    file = models.FileField(upload_to="chat_files/", null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    reaction = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return f"{self.sender.username}: {self.textor or self.file.name}"

class MessageReaction(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="reactions")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)  
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("message", "user", "emoji")