from django.db import models
from django.conf import settings

class Group(models.Model):
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="user_groups")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class GroupFile(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="files")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_files")  # related_name eklendi
    file = models.FileField(upload_to="uploads/")
    filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    one_time_view = models.BooleanField(default=False)
    has_been_viewed = models.BooleanField(default=False)

    VIEW_DURATIONS = [
        ("10s", "10 saniye"),
        ("30s", "30 saniye"),
        ("1m", "1 dakika"),
        ("5m", "5 dakika"),
        ("1h", "1 saat"),
        ("video", "Video suresi"),
        ("unlimited", "Suresiz"),
    ]
    view_duration = models.CharField(max_length=20, choices=VIEW_DURATIONS, default="unlimited")
    watermark_enabled = models.BooleanField(default=True)
    
    def __str__(self):
        return self.filename

class Comment(models.Model):
    file = models.ForeignKey(GroupFile, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_comments")  # related_name eklendi
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.text[:20]}"

class FileViewLog(models.Model):
    file = models.ForeignKey(GroupFile, on_delete=models.CASCADE, related_name="view_logs")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="file_view_logs")  # related_name eklendi
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} → {self.file.filename} @ {self.viewed_at}"