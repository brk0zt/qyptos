from django.utils import timezone
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from notifications.models import Notification
from notifications.utils import send_notification
from .models import Group, GroupFile, Comment, FileViewLog
from .serializers import GroupFileSerializer, CommentSerializer, FileViewLogSerializer

class FileDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        file = get_object_or_404(GroupFile, id=file_id)

        if file.one_time_view and file.has_been_viewed:
            return Response({"error": "Bu dosya sadece tek seferlik görüntülenebilir."}, status=403)

        # İlk görüntüleme → flag ve log kaydı
        if file.one_time_view and not file.has_been_viewed:
            file.has_been_viewed = True
            file.save()

        # Log kaydı (her indirmede/görüntülemede)
        FileViewLog.objects.create(file=file, user=request.user)

        return FileResponse(file.file.open("rb"), as_attachment=True, filename=file.filename)

class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(Group, id=group_id)
        uploaded_file = request.FILES["file"]

        one_time_view = request.data.get("one_time_view", "false").lower() == "true"
        view_duration = request.data.get("view_duration", "unlimited")
        watermark_enabled = request.data.get("watermark_enabled", "true").lower() == "true"

        file_instance = GroupFile.objects.create(
            group=group,
            uploaded_by=request.user,
            file=uploaded_file,
            filename=uploaded_file.name,
            one_time_view=one_time_view,
            view_duration=view_duration,
            watermark_enabled=watermark_enabled,
        )

        # Bildirim gönderme kodu
        members = group.members.all()
        for member in members:
            if member != request.user:
                notif = Notification.objects.create(
                    user=member,
                    text=f"{request.user.username}, {group.name} grubuna yeni dosya yükledi.",
                    target_url=f"/groups/{group.id}/files/{file_instance.id}"
                )
                send_notification(member.id, {
                    "id": notif.id,
                    "text": notif.text,
                    "target_url": notif.target_url
                })

        return Response(
            {
                "message": "Dosya yüklendi!",
                "id": file_instance.id,
                "one_time_view": file_instance.one_time_view,
                "view_duration": file_instance.view_duration,
                "watermark_enabled": file_instance.watermark_enabled,
            },
            status=201,
        )

class CommentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, file_id):
        file = get_object_or_404(GroupFile, id=file_id)
        text = request.data.get("text")

        comment = Comment.objects.create(
            file=file,
            user=request.user,
            text=text,
        )

        if file.uploaded_by != request.user:
            notif = Notification.objects.create(
                user=file.uploaded_by,
                text=f"{request.user.username}, dosyana yorum yaptı: {text[:30]}..."
            )
            send_notification(file.uploaded_by.id, {"id": notif.id, "text": notif.text})

        return Response({"message": "Yorum eklendi!"}, status=201)

class FileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        file = get_object_or_404(GroupFile, id=file_id)
        file_data = GroupFileSerializer(file).data

        # Tek seferlik görüntüleme
        if file.one_time_view and not file.has_been_viewed:
            file_data["view_url"] = f"http://127.0.0.1:8001/groups/files/{file.id}/download/"
            file_data["watermark"] = {
                "username": request.user.username,
                "timestamp": timezone.now().isoformat()
            }
            file_data["view_duration"] = file.view_duration
        else:
            file_data["view_url"] = None
            file_data["watermark"] = None
            file_data["view_duration"] = "expired"

        comments = CommentSerializer(file.comments.all().order_by("-created_at"), many=True).data
        return Response({"file": file_data, "comments": comments})

class FileReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        file = get_object_or_404(GroupFile, id=file_id, uploaded_by=request.user)

        logs = FileViewLog.objects.filter(file=file).order_by("-viewed_at")
        serializer = FileViewLogSerializer(logs, many=True)

        return Response({
            "file": file.filename,
            "total_views": logs.count(),
            "logs": serializer.data
        })