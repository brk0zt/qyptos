from rest_framework import serializers
from .models import ChatThread, Message, UserStatus, MessageReaction
from django.contrib.auth import get_user_model

User = get_user_model()

class UserStatusSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    
    class Meta:
        model = UserStatus
        fields = ['user_id', 'username', 'is_online', 'last_seen']

class ReactionSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = MessageReaction
        fields = ["id", "user", "emoji"]

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_id = serializers.IntegerField(source='sender.id', read_only=True)
    file_url = serializers.SerializerMethodField()
    reactions = ReactionSerializer(many=True, read_only=True)

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None

    class Meta:
        model = Message
        fields = ["id", "sender_id", "sender_username", "text", "file_url", "timestamp", "read", "reactions"]

class ChatThreadSerializer(serializers.ModelSerializer):
    user1 = UserStatusSerializer(read_only=True)
    user2 = UserStatusSerializer(read_only=True)
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatThread
        fields = ["id", "user1", "user2", "messages"]

class MessageSerializer(serializers.ModelSerializer):
    sender = UserStatusSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    reactions = ReactionSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = ["id", "sender", "text", "file_url", "timestamp", "read", "reactions"]

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None
