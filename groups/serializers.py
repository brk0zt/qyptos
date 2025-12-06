from rest_framework import serializers
from .models import GroupFile, Comment, FileViewLog, Group, GroupInvitation

class GroupFileSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.CharField(source="uploaded_by.username", read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)
    comment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = GroupFile
        fields = [
            "id", "group", "group_name", "uploaded_by", "file", "filename", 
            "created_at", "one_time_view", "has_been_viewed", 
            "view_duration", "watermark_enabled", "comment_count", "file_type", "file_size"
                 ]
        read_only_fields = ["uploaded_by", "created_at", "has_been_viewed", "filename"]
    
    def get_comment_count(self, obj):
        return obj.comments.count()

class PublicFileSearchSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.CharField(source="uploaded_by.username", read_only=True)
    group_name = serializers.CharField(source="group.name", read_only=True)
    uploaded_at = serializers.DateTimeField(source="created_at", read_only=True)
    download_url = serializers.SerializerMethodField()
    
    class Meta:
        model = GroupFile
        fields = [
            "id", "filename", "file_type", "file_size", "uploaded_by",
            "group_name", "uploaded_at", "download_url", "watermark_enabled"
        ]
    
    def get_download_url(self, obj):
        return f"/api/files/{obj.id}/download/"

class SearchStatsSerializer(serializers.Serializer):
    total_files = serializers.IntegerField()
    file_types = serializers.DictField()
    total_size = serializers.IntegerField()

class GroupSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    created_by = serializers.CharField(source="created_by.username", read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    invite_code = serializers.CharField(read_only=True)
    is_public = serializers.BooleanField()

    class Meta:
        model = Group
        fields = ['id', 'name', 'members', 'created_at', 'member_count', 'created_by', 'is_verified', 'is_public', 'invite_code']
        extra_kwargs = {
            'members': {'required': False, 'allow_empty': True}  
        }
    
    def get_member_count(self, obj):
        return obj.members.count()

    def create(self, validated_data):
        # Remove members from validated_data if present
        members_data = validated_data.pop('members', [])
    
        # Create the group
        group = Group.objects.create(**validated_data)
    
        # Add the creator as a member
        if self.context.get('request'):
            group.members.add(self.context['request'].user)
            # created_by is automatically set by the model
    
        return group

class GroupInvitationSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)
    inviter_username = serializers.CharField(source='inviter.username', read_only=True)

    class Meta:
        model = GroupInvitation
        fields = ['id', 'group', 'group_name', 'inviter', 'inviter_username', 'email', 'token', 'status', 'created_at']
        read_only_fields = ['token', 'inviter']

class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    user = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "user", "text", "created_at", "replies", "parent"]

    def get_replies(self, obj):
        replies = obj.replies.all().order_by("created_at")
        return CommentSerializer(replies, many=True).data

class FileViewLogSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source="user.username")

    class Meta:
        model = FileViewLog
        fields = ["user", "viewed_at"]