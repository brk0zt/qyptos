# models.py
from django.db import models
from django.conf import settings

# Group modelini EN BAŞTA tanımla
class Group(models.Model):
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="user_groups")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_groups", null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    invite_code = models.CharField(max_length=10, unique=True, blank=True, null=True)
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.invite_code:
            self.invite_code = self.generate_invite_code()
        super().save(*args, **kwargs)
    
    def generate_invite_code(self):
        import random
        import string
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

class GroupInvitation(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="invitations")
    inviter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="sent_invitations")
    invited_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="received_invitations", null=True, blank=True)
    email = models.EmailField(blank=True)
    token = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Bekliyor'), ('accepted', 'Kabul Edildi'), ('rejected', 'Reddedildi')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"{self.group.name} - {self.email}"

# GroupFile modelini Group'tan SONRA tanımla
class GroupFile(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="files")
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="group_files")
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
    
    # Arama için yeni alanlar
    search_index = models.TextField(blank=True)
    file_type = models.CharField(max_length=50, blank=True)
    file_size = models.BigIntegerField(default=0)
    
    def __str__(self):
        return self.filename
    
    def save(self, *args, **kwargs):
        # Dosya türünü ve boyutunu otomatik belirle
        if self.file:
            self.filename = self.file.name
            self.file_size = self.file.size
            # Dosya uzantısından türünü belirle
            import os
            ext = os.path.splitext(self.filename)[1].lower()
            self.file_type = self.get_file_type(ext)
            
            # Arama indeksini oluştur
            self.update_search_index()
        
        super().save(*args, **kwargs)
    
    def get_file_type(self, extension):
        file_types = {
            '.pdf': 'PDF',
            '.doc': 'Word',
            '.docx': 'Word',
            '.txt': 'Text',
            '.jpg': 'Image',
            '.jpeg': 'Image',
            '.png': 'Image',
            '.gif': 'Image',
            '.mp4': 'Video',
            '.avi': 'Video',
            '.mov': 'Video',
            '.mp3': 'Audio',
            '.wav': 'Audio',
            '.zip': 'Archive',
            '.rar': 'Archive',
        }
        return file_types.get(extension, 'Other')
    
    def update_search_index(self):
        """Arama indeksini güncelle"""
        index_parts = [
            self.filename,
            self.uploaded_by.username if self.uploaded_by else "",
            self.group.name if self.group else "",
            self.file_type,
        ]
        self.search_index = " ".join(part.lower() for part in index_parts if part)

class Comment(models.Model):
    file = models.ForeignKey(GroupFile, on_delete=models.CASCADE, related_name="comments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.text[:30]}"

class FileViewLog(models.Model):
    file = models.ForeignKey(GroupFile, on_delete=models.CASCADE, related_name="view_logs")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="file_view_logs")
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} → {self.file.filename} @ {self.viewed_at}"