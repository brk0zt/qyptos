import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db import models

class MediaFile(models.Model):
    file = models.FileField(upload_to="media_files/")
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    single_view = models.BooleanField(default=False)
    consumed_by = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="consumed_media")

    def __str__(self):
        return self.file.name


def upload_path(instance, filename):
    return f"uploads/{instance.owner_id}/{filename}"

class File(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to=upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    one_time_view = models.BooleanField(default=False)
    has_been_viewed = models.BooleanField(default=False)
    view_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return self.file.name

class CloudGroup(models.Model):
    name = models.CharField(max_length=255)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_groups')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='cloud_groups', blank=True)
    invite_token = models.CharField(max_length=255, unique=True, blank=True)
    is_public = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.invite_token:
            self.invite_token = str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class GroupFile(models.Model):
    group = models.ForeignKey(CloudGroup, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='group_files/')
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True) 
    one_time_view = models.BooleanField(default=False)
    has_been_viewed = models.BooleanField(default=False)
    view_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.file.name} in {self.group.name}"

class GroupInvite(models.Model):
    group = models.ForeignKey(CloudGroup, on_delete=models.CASCADE, related_name="invites")
    email = models.EmailField()
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.email} -> {self.group.name}"

class SecureLink(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name="secure_links")
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    max_uses = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)

    def is_valid(self):
        return self.used_count < self.max_uses and timezone.now() < self.expires_at

    def __str__(self):
        return f"SecureLink for {self.file}"

class GroupMember(models.Model):
    ROLE_CHOICES = (
        ('member', 'Member'),
        ('admin', 'Admin'),
        ('owner', 'Owner'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.ForeignKey(CloudGroup, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    
    class Meta:
        unique_together = ('user', 'group')

    def __str__(self):
        return f"{self.user.username} - {self.group.name} ({self.role})"

class FileComment(models.Model):
    file = models.ForeignKey(GroupFile, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Comment by {self.author.username}"

class GroupFeed(models.Model):
    FEED_TYPES = (
        ("file_upload", "File Upload"),
        ("comment", "Comment"),
        ("announcement", "Announcement"),
    )

    group = models.ForeignKey(CloudGroup, on_delete=models.CASCADE, related_name="feed")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    feed_type = models.CharField(max_length=20, choices=FEED_TYPES)
    content = models.TextField(blank=True, null=True)
    related_file = models.ForeignKey(GroupFile, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.group.name} - {self.feed_type} - {self.user.username}"

class Ad(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to="ads/", null=True, blank=True)
    link = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class UserEarning(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="earnings")
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.amount}₺"

class Device(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="devices")
    device_uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    device_name = models.CharField(max_length=255, blank=True, null=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.device_name or self.device_uuid}"
