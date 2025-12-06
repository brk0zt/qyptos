from django.contrib import admin
from .models import MemoryTier, MemoryItem, UserActivity

@admin.register(MemoryTier)
class MemoryTierAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration_minutes']

@admin.register(MemoryItem)
class MemoryItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'file_path', 'file_type', 'memory_tier', 'created_at']
    list_filter = ['file_type', 'memory_tier', 'created_at']

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type', 'timestamp']
    list_filter = ['activity_type', 'timestamp']