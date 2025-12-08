# -*- coding: utf-8 -*-
# memory/models.py
from django.conf import settings
from django.db import models
from django.contrib.auth.models import User
import json
from datetime import datetime, timedelta
from django.utils import timezone

class MemoryTier(models.Model):
    TIER_CHOICES = [
        # duration_minutes: Instant için 5, Short Term için 24*60=1440, Long Term için 30*24*60=43200
        ('instant', 'Instant Recall'), 
        ('short_term', 'Short Term'), 
        ('long_term', 'Long Term'),
    ]
    name = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    # duration_minutes: Süre sonunu save() yerine MemoryTier'da merkezileştirdik.
    duration_minutes = models.PositiveIntegerField(default=1440) # default 1 gün (short term)
    
    def __str__(self):
        return self.name

    def get_expiration_timedelta(self):
        """Bu katman icin timedelta nesnesini dondurur"""
        return timedelta(minutes=self.duration_minutes)

class UserMemoryProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    learning_rate = models.FloatField(default=0.1)
    last_activity = models.DateTimeField(auto_now=True)
    total_memory_used_mb = models.FloatField(default=0)
    memory_quota_mb = models.FloatField(default=1024)  # 1GB default quota
    
    def __str__(self):
        return f"{self.user.username} Memory Profile"

class MemoryItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file_path = models.CharField(max_length=500)
    file_name = models.CharField(max_length=255, blank=True, null=True)  # Eklendi
    file_type = models.CharField(max_length=50)
    original_size = models.BigIntegerField()
    
    # Vector representation
    vector_embedding = models.BinaryField(null=True, blank=True)
    compressed_embedding = models.BinaryField(null=True, blank=True)  # Eklendi
    
    # --- YENİ SEMANTİK GRAFİK SIKIŞTIRMA ALANLARI ---
    is_semantically_compressed = models.BooleanField(default=False)
    
    # 1. Semantik Özellik Vektörleri (GNN/Transformer'dan gelen x_final)
    # BinaryField, numpy/torch tensörünü bayt olarak saklamak için idealdir.
    semantic_features = models.BinaryField(null=True, blank=True) 
    
    # 2. Grafik Topolojisi (Kırpılmış Edge Index)
    # Zlib ile sıkıştırılmış numpy array (topoloji verisini tutar)
    graph_topology = models.BinaryField(null=True, blank=True) 
    
    # 3. Süperpiksel Haritası (Geri oluşturma için piksellerin hangi düğüme ait olduğunu tutar)
    superpixel_map = models.BinaryField(null=True, blank=True) 
    
    # 4. Grafik Meta Verileri (Düğüm sayısı, özellik boyutu, vb.)
    graph_metadata = models.JSONField(default=dict)

    # Structural representation
    structural_data = models.TextField()
    
    memory_tier = models.ForeignKey(MemoryTier, on_delete=models.CASCADE)
    access_count = models.IntegerField(default=0)
    last_accessed = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)  # Eklendi
    
    # Semantic information
    semantic_tags = models.JSONField(default=list)
    content_summary = models.TextField(blank=True, null=True)  # Eklendi
    
    # Screenshot/thumbnail info
    thumbnail_path = models.CharField(max_length=500, blank=True, null=True)  # Eklendi
    window_title = models.CharField(max_length=255, blank=True, null=True)  # Eklendi
    application_name = models.CharField(max_length=100, blank=True, null=True)  # Eklendi
    
    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Basit süre sonu hesaplama
            from datetime import timedelta
            from django.utils import timezone
            
            if self.memory_tier.name == 'instant':
                self.expires_at = timezone.now() + timedelta(minutes=5)
            elif self.memory_tier.name == 'short_term':
                self.expires_at = timezone.now() + timedelta(hours=24)
            else:  # long_term
                self.expires_at = timezone.now() + timedelta(days=30)
        
        if not self.file_name and self.file_path:
            import os
            self.file_name = os.path.basename(self.file_path)
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.file_name} ({self.memory_tier})"

class UserActivity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50)  # 'file_open', 'file_save', 'search', 'app_switch'
    target_file = models.CharField(max_length=500, null=True, blank=True)
    application = models.CharField(max_length=100, blank=True, null=True)
    window_title = models.CharField(max_length=255, blank=True, null=True)
    context = models.JSONField(default=dict)
    screenshot_path = models.CharField(max_length=500, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['user', 'activity_type']),
        ]
        ordering = ['-timestamp']

class TimelineEvent(models.Model):
    """Windows Recall benzeri timeline event'leri"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    event_type = models.CharField(max_length=50)  # 'file_activity', 'browser_history', 'app_usage'
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    thumbnail = models.CharField(max_length=500, blank=True, null=True)
    metadata = models.JSONField(default=dict)
    confidence_score = models.FloatField(default=1.0)
    
    class Meta:
        indexes = [
            models.Index(fields=['user', 'timestamp']),
        ]
        ordering = ['-timestamp']


class VideoFrame(models.Model):
    """
    Bir videonun belirli bir anındaki görüntünün vektör karşılığı.
    """
    memory_item = models.ForeignKey(MemoryItem, on_delete=models.CASCADE, related_name='video_frames')
    timestamp = models.FloatField(help_text="Videonun kaçıncı saniyesi")
    vector_embedding = models.BinaryField(help_text="Bu karenin CLIP vektörü")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.memory_item.file_name} - {self.timestamp}s"