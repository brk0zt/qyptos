from notifications.models import Notification
from notifications.utils import send_notification

class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(Group, id=group_id)
        uploaded_file = request.FILES["file"]

        file_instance = GroupFile.objects.create(
            group=group,
            uploaded_by=request.user,
            file=uploaded_file,
        )

        members = group.members.exclude(id=request.user.id)
        for member in members:
            notif = Notification.objects.create(
                user=member,
                text=f"{request.user.username}, {group.name} grubuna yeni dosya yükledi."
            )
            send_notification(member.id, {"id": notif.id, "text": notif.text})

        return Response({"message": "Dosya yüklendi!"}, status=201)

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

        # Bildirim → dosya sahibine (kendine değil)
        if file.uploaded_by != request.user:
            notif = Notification.objects.create(
                user=file.uploaded_by,
                text=f"{request.user.username}, dosyana yorum yaptı: {text[:30]}..."
            )
            send_notification(file.uploaded_by.id, {"id": notif.id, "text": notif.text})

        return Response({"message": "Yorum eklendi!"}, status=201)

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