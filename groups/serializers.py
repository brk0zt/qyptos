from rest_framework import serializers
from .models import GroupFile, Comment, FileViewLog

class GroupFileSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.CharField(source="uploaded_by.username")
    class Meta:
        model = GroupFile
        fields = ['id', 'group', 'uploaded_by', 'file', 'filename', 'created_at', 
                  'one_time_view', 'has_been_viewed', 'view_duration', 'watermark_enabled']

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="user.username")
    class Meta:
        model = Comment
        fields = ['id', 'file', 'author', 'text', 'created_at']

class FileViewLogSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username")

    class Meta:
        model = FileViewLog
        fields = ["user", "viewed_at"]