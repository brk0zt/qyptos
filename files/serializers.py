from rest_framework import serializers
from .models import File, CloudGroup, GroupFile, FileComment, GroupInvite, GroupFeed, Ad, UserEarning, SecureLink, MediaFile

class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = ["id", "file", "uploader", "single_view", "consumed_by"]
        read_only_fields = ["uploader", "consumed_by"]

class SecureLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecureLink
        fields = ["id", "token", "file", "expires_at", "max_uses", "used_count"]

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id','file','uploaded_at','one_time_view','viewed','view_token','is_public']
        read_only_fields = ['uploaded_at','has_been_viewed','view_token']

class CloudGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CloudGroup
        fields = ['id','name','owner','invite_token','is_public']

class GroupFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupFile
        fields = ['id','group','file','uploader','uploaded_at','one_time_view','has_been_viewed','view_token','is_public']
        read_only_fields = ['uploader','uploaded_at','has_been_viewed','view_token']

class FileCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileComment
        fields = ['id','file','author','content','created_at']
        read_only_fields = ['author','created_at']

class GroupInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupInvite
        fields = ["id", "group", "email", "invited_by", "created_at", "accepted"]
        read_only_fields = ["invited_by", "created_at", "accepted"]

class GroupFeedSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    group = serializers.StringRelatedField()
    related_file = serializers.StringRelatedField()

    class Meta:
        model = GroupFeed
        fields = ["id", "group", "user", "feed_type", "content", "related_file", "created_at"]

class AdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = ["id", "title", "image", "link", "is_active"]


class UserEarningSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = UserEarning
        fields = ["id", "user", "amount", "updated_at"]
