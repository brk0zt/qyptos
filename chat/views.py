from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import ChatThread, Message, UserStatus
from .serializers import ChatThreadSerializer, MessageSerializer
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class UserListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.exclude(id=request.user.id)
        user_data = []
        for user in users:
            try:
                user_status = UserStatus.objects.get(user=user)
                is_online = user_status.is_online
                last_seen = user_status.last_seen
            except UserStatus.DoesNotExist:
                is_online = False
                last_seen = None
                
            user_data.append({
                'id': user.id,
                'username': user.username,
                'is_online': is_online,
                'last_seen': last_seen
            })
        
        user_data.sort(key=lambda x: (not x['is_online'], x['username'].lower()))
        return Response(user_data)

class ChatThreadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        user2 = get_object_or_404(User, id=user_id)
        thread, created = ChatThread.objects.get_or_create(
            user1=min(request.user, user2, key=lambda u: u.id),
            user2=max(request.user, user2, key=lambda u: u.id),
        )
        serializer = ChatThreadSerializer(thread)
        return Response(serializer.data)

class MessageListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, thread_id):
        thread = get_object_or_404(ChatThread, id=thread_id)
        if request.user not in [thread.user1, thread.user2]:
            return Response({"error": "Bu sohbete erisimin yok."}, status=403)
        messages = thread.messages.order_by("timestamp")
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

class FileUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "Dosya yok"}, status=400)
        message = Message.objects.create(
            thread_id=request.data.get("thread_id"),
            sender=request.user,
            file=file
        )
        return Response(MessageSerializer(message).data, status=201)

class DeleteMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, message_id):
        message = get_object_or_404(Message, id=message_id)
        if message.sender != request.user:
            return Response({"error": "Bu mesaji silme yetkin yok."}, status=403)
        message.delete()
        return Response({"message": "Mesaj silindi."}, status=204)

class EditMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, message_id):
        message = get_object_or_404(Message, id=message_id)
        if message.sender != request.user:
            return Response({"error": "Bu mesaji duzenleme yetkin yok."}, status=403)

        new_text = request.data.get("text", "")
        message.text = new_text
        message.save()

        return Response({
            "id": message.id,
            "text": message.text,
            "edited": True
        }, status=status.HTTP_200_OK)

class MarkAsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, message_id):
        message = get_object_or_404(Message, id=message_id)

        # Mesajý gönderen kiţi kendisi olamaz, sadece karţý taraf okundu olarak iţaretleyebilir
        if message.sender == request.user:
            return Response({"error": "Kendi mesajini okunmus yapamazsin."}, status=403)

        message.read = True
        message.save()
        return Response({"message": "Mesaj okundu olarak isaretlendi."})

class ToggleReactionView(APIView):  # Added the missing class
    permission_classes = [IsAuthenticated]

    def post(self, request, message_id):
        message = get_object_or_404(Message, id=message_id)
        
        # Check if user has access to this message
        if request.user not in [message.thread.user1, message.thread.user2]:
            return Response({"error": "Bu mesaja erisimin yok."}, status=403)
        
        emoji = request.data.get("emoji", "")
        
        # If the emoji is empty, remove reaction
        if not emoji:
            message.reaction = ""
            message.save()
            return Response({"message": "Reaction removed."})
        
        # Set the reaction
        message.reaction = emoji
        message.save()
        
        return Response({
            "id": message.id,
            "reaction": message.reaction
        })