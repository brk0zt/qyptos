
from rest_framework import permissions, status, views
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import CloudGroup, GroupMembership, GroupFile, FileComment

class AddAdminView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(CloudGroup, id=group_id)
        if not GroupMembership.objects.filter(user=request.user, group=group, role="owner").exists():
            return Response({"error": "Sadece owner admin atayabilir"}, status=status.HTTP_403_FORBIDDEN)
        
        username = request.data.get("username")
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "Kullanıcı bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

        membership, _ = GroupMembership.objects.get_or_create(user=user, group=group)
        membership.role = "admin"
        membership.save()
        return Response({"message": f"{username} artık admin"})
    

class RemoveMemberView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(CloudGroup, id=group_id)
        membership = GroupMembership.objects.filter(user=request.user, group=group).first()
        if not membership or membership.role not in ["owner", "admin"]:
            return Response({"error": "Sadece admin veya owner üye çıkarabilir"}, status=status.HTTP_403_FORBIDDEN)

        username = request.data.get("username")
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"error": "Kullanıcı bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

        GroupMembership.objects.filter(user=user, group=group).delete()
        return Response({"message": f"{username} gruptan çıkarıldı"})
    

class DeleteGroupFileView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, file_id):
        file = get_object_or_404(GroupFile, id=file_id)
        membership = GroupMembership.objects.filter(user=request.user, group=file.group).first()
        if not membership or membership.role not in ["owner", "admin"]:
            return Response({"error": "Dosya silmek için admin veya owner olmalısınız"}, status=status.HTTP_403_FORBIDDEN)
        
        file.file.delete()
        file.delete()
        return Response({"message": "Dosya silindi"})


class AddFileCommentView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, file_id):
        file = get_object_or_404(GroupFile, id=file_id)
        if not GroupMembership.objects.filter(user=request.user, group=file.group).exists():
            return Response({"error": "Yorum yapmak için grup üyesi olmalısınız"}, status=status.HTTP_403_FORBIDDEN)

        content = request.data.get("content")
        if not content:
            return Response({"error": "Yorum boş olamaz"}, status=status.HTTP_400_BAD_REQUEST)

        comment = FileComment.objects.create(file=file, author=request.user, content=content)
        return Response({"message": "Yorum eklendi", "id": comment.id, "content": comment.content, "author": request.user.username})
