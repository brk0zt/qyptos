from django.utils import timezone
from django.http import FileResponse, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from notifications.models import Notification
from notifications.utils import send_notification
from .models import Group, GroupFile, Comment, FileViewLog, GroupInvitation
from .serializers import GroupFileSerializer, CommentSerializer, FileViewLogSerializer, GroupSerializer, GroupInvitationSerializer, PublicFileSearchSerializer, SearchStatsSerializer
from django.db.models import Count
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
import csv
from io import StringIO, BytesIO
from reportlab.pdfgen import canvas
import re
from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework import generics, permissions
from django.db.models import Q, Count, Sum
from django.db.models.functions import Lower
import operator
from functools import reduce

User = get_user_model()

MENTION_PATTERN = re.compile(r"@(\w+)")

def handle_mentions(text, sender):
    channel_layer = get_channel_layer()
    usernames = MENTION_PATTERN.findall(text)
    for username in usernames:
        try:
            mentioned_user = User.objects.get(username=username)
            Notification.objects.create(
                user=mentioned_user,
                message=f"{sender.username} seni bir yorumda etiketledi.",
            )
            async_to_sync(channel_layer.group_send)(
                f"user_{mentioned_user.id}",
                {
                    "type": "send_notification",
                    "content": {
                        "title": "Yeni Mention 🔔",
                        "message": f"{sender.username} seni bir yorumda etiketledi.",
                    },
                },
            )
        except User.DoesNotExist:
            continue

class PublicFileSearchView(APIView):
    """
    Halka açık dosyalarda arama yapar
    """
    permission_classes = []  # Herkese açık
    
    def get(self, request):
        query = request.GET.get('q', '').strip()
        file_type = request.GET.get('type', '')
        sort_by = request.GET.get('sort', 'recent')  # recent, popular, size, name
        
        if not query and not file_type:
            return Response({"error": "Arama terimi veya dosya türü gereklidir"}, status=400)
        
        # Halka açık gruplardaki dosyaları filtrele
        files = GroupFile.objects.filter(group__is_public=True)
        
        # Arama sorgusu
        if query:
            # Arama terimlerini ayır ve her biri için arama yap
            search_terms = query.split()
            search_queries = []
            
            for term in search_terms:
                search_queries.extend([
                    Q(filename__icontains=term),
                    Q(uploaded_by__username__icontains=term),
                    Q(group__name__icontains=term),
                    Q(search_index__icontains=term.lower())
                ])
            
            # OR koşulu ile tüm arama terimlerini birleştir
            files = files.filter(reduce(operator.or_, search_queries))
        
        # Dosya türüne göre filtrele
        if file_type:
            files = files.filter(file_type=file_type)
        
        # Sıralama
        if sort_by == 'popular':
            files = files.annotate(view_count=Count('view_logs')).order_by('-view_count', '-created_at')
        elif sort_by == 'size':
            files = files.order_by('-file_size', '-created_at')
        elif sort_by == 'name':
            files = files.order_by(Lower('filename'))
        else:  # recent (varsayılan)
            files = files.order_by('-created_at')
        
        # Sayfalama
        page_size = min(int(request.GET.get('limit', 20)), 100)  # Maksimum 100 sonuç
        files = files[:page_size]
        
        serializer = PublicFileSearchSerializer(files, many=True)
        
        return Response({
            "query": query,
            "results": serializer.data,
            "total_results": files.count(),
            "filters": {
                "file_type": file_type,
                "sort_by": sort_by
            }
        })

class SearchSuggestionsView(APIView):
    """
    Arama önerileri sağlar
    """
    permission_classes = []  # Herkese açık
    
    def get(self, request):
        query = request.GET.get('q', '').strip()
        
        if len(query) < 2:
            return Response({"suggestions": []})
        
        # Halka açık gruplardaki dosyalarda arama
        files = GroupFile.objects.filter(
            group__is_public=True
        ).filter(
            Q(filename__icontains=query) |
            Q(group__name__icontains=query)
        )[:10]  # İlk 10 öneri
        
        suggestions = []
        
        # Dosya isimlerinden öneriler
        for file in files:
            suggestions.append({
                "type": "file",
                "name": file.filename,
                "group": file.group.name,
                "file_type": file.file_type
            })
        
        # Grup isimlerinden öneriler
        groups = Group.objects.filter(
            is_public=True,
            name__icontains=query
        )[:5]
        
        for group in groups:
            suggestions.append({
                "type": "group",
                "name": group.name,
                "member_count": group.members.count()
            })
        
        return Response({"suggestions": suggestions[:15]})  # Maksimum 15 öneri

class SearchStatsView(APIView):
    """
    Arama istatistiklerini sağlar
    """
    permission_classes = []  # Herkese açık
    
    def get(self, request):
        # Halka açık gruplardaki dosyaların istatistikleri
        stats = GroupFile.objects.filter(group__is_public=True).aggregate(
            total_files=Count('id'),
            total_size=Sum('file_size'),
            file_types=Count('file_type')
        )
        
        # Dosya türlerine göre dağılım
        file_type_stats = GroupFile.objects.filter(
            group__is_public=True
        ).values('file_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        file_types_dict = {item['file_type']: item['count'] for item in file_type_stats}
        
        return Response({
            "total_files": stats['total_files'] or 0,
            "total_size": stats['total_size'] or 0,
            "file_types": file_types_dict,
            "total_size_gb": round((stats['total_size'] or 0) / (1024**3), 2)
        })

class PopularSearchesView(APIView):
    """
    Popüler aramaları ve trend dosyaları listeler
    """
    permission_classes = []  # Herkese açık
    
    def get(self, request):
        # En çok görüntülenen dosyalar (popüler)
        popular_files = GroupFile.objects.filter(
            group__is_public=True
        ).annotate(
            view_count=Count('view_logs')
        ).order_by('-view_count')[:10]
        
        # Yeni yüklenen dosyalar (trend)
        recent_files = GroupFile.objects.filter(
            group__is_public=True
        ).order_by('-created_at')[:10]
        
        popular_serializer = PublicFileSearchSerializer(popular_files, many=True)
        recent_serializer = PublicFileSearchSerializer(recent_files, many=True)
        
        return Response({
            "popular_files": popular_serializer.data,
            "recent_files": recent_serializer.data
        })

# Kullanıcı Profili View'ı
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email
        })

# Grup Listesi View'ı
class GroupListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Kullanıcının üye olduğu gruplar
        groups = Group.objects.filter(members=request.user)
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)

# Grup Oluşturma View'ı
class GroupCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get data from request
        name = request.data.get('name')
        is_public = request.data.get('is_public', True)
        
        if not name:
            return Response({"error": "Grup adı gereklidir"}, status=400)
        
        # Create group with serializer
        data = {
            'name': name,
            'is_public': is_public
        }
        
        serializer = GroupSerializer(data=data, context={'request': request})
        
        if serializer.is_valid():
            group = serializer.save()
            return Response(serializer.data, status=201)
        else:
            return Response(serializer.errors, status=400)

# Gruba Katılma View'ı
class GroupJoinView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(Group, id=group_id)
        
        # Kullanıcı zaten grupta mı?
        if group.members.filter(id=request.user.id).exists():
            return Response({"error": "Zaten bu gruptasınız"}, status=400)
        
        # Kullanıcıyı gruba ekle
        group.members.add(request.user)
        
        return Response({"message": "Gruba katıldınız!"})

# Gruptan Ayrılma View'ı
class GroupLeaveView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(Group, id=group_id)
        
        # Kullanıcı grupta mı?
        if not group.members.filter(id=request.user.id).exists():
            return Response({"error": "Bu grupta değilsiniz"}, status=400)
        
        # Kullanıcıyı gruptan çıkar
        group.members.remove(request.user)
        
        return Response({"message": "Gruptan ayrıldınız"})

# Grup Yetki Kontrolü View'ı
class GroupAuthCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        group = get_object_or_404(Group, id=group_id)
        # Kullanıcının bu gruba üye olup olmadığını kontrol et
        is_member = group.members.filter(id=request.user.id).exists()
        return Response({"authorized": is_member})


    # views.py - Yeni view'lar ekle
class GroupInviteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(Group, id=group_id)
        
        # Sadece grup üyeleri davet gönderebilir
        if not group.members.filter(id=request.user.id).exists():
            return Response({"error": "Bu grup için davet gönderme izniniz yok."}, status=403)
        
        emails = request.data.get('emails', [])
        if not emails:
            return Response({"error": "En az bir email adresi gereklidir."}, status=400)
        
        invitations = []
        for email in emails:
            # Token oluştur
            import secrets
            token = secrets.token_urlsafe(32)
            
            invitation = GroupInvitation.objects.create(
                group=group,
                inviter=request.user,
                email=email,
                token=token,
                expires_at=timezone.now() + timezone.timedelta(days=7)
            )
            invitations.append(invitation)
            
            # Burada email gönderme işlemi yapılabilir
            # send_invitation_email(email, token, group.name, request.user.username)
        
        serializer = GroupInvitationSerializer(invitations, many=True)
        return Response(serializer.data, status=201)

class GroupJoinByInviteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, token):
        invitation = get_object_or_404(GroupInvitation, token=token)
        
        # Davetin geçerli olup olmadığını kontrol et
        if invitation.status != 'pending':
            return Response({"error": "Bu davet geçersiz."}, status=400)
        
        if invitation.expires_at < timezone.now():
            return Response({"error": "Bu davetin süresi dolmuş."}, status=400)
        
        # Kullanıcıyı gruba ekle
        group = invitation.group
        group.members.add(request.user)
        
        # Davet durumunu güncelle
        invitation.status = 'accepted'
        invitation.invited_user = request.user
        invitation.save()
        
        return Response({"message": "Gruba katıldınız!"})

class GroupInviteByCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        invite_code = request.data.get('invite_code')
        if not invite_code:
            return Response({"error": "Davet kodu gereklidir."}, status=400)
        
        group = get_object_or_404(Group, invite_code=invite_code)
        
        # Kullanıcı zaten grupta mı?
        if group.members.filter(id=request.user.id).exists():
            return Response({"error": "Zaten bu gruptasınız."}, status=400)
        
        # Kullanıcıyı gruba ekle
        group.members.add(request.user)
        
        return Response({"message": "Gruba katıldınız!", "group": GroupSerializer(group).data})

class GroupInvitationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        group = get_object_or_404(Group, id=group_id)
        
        # Sadece grup üyeleri davetleri görebilir
        if not group.members.filter(id=request.user.id).exists():
            return Response({"error": "Bu grubun davetlerini görme izniniz yok."}, status=403)
        
        invitations = GroupInvitation.objects.filter(group=group)
        serializer = GroupInvitationSerializer(invitations, many=True)
        return Response(serializer.data)


# Grup Dosyaları View'ı
class GroupFilesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        group = get_object_or_404(Group, id=group_id)
        # Kullanıcının gruba üye olup olmadığını kontrol et
        if not group.members.filter(id=request.user.id).exists():
            return Response({"error": "Bu gruba erişim izniniz yok."}, status=403)
        files = GroupFile.objects.filter(group=group)
        serializer = GroupFileSerializer(files, many=True)
        return Response(serializer.data)

# Dosya Yorumları View'ı
class FileCommentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        file = get_object_or_404(GroupFile, id=file_id)
        comments = Comment.objects.filter(file=file)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

# Mevcut view'larınızı buraya kopyalayın (FileDownloadView, FileUploadView, vb.)
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

# DÜZELTİLMİŞ: CommentCreateView - FileUploadView dışına taşındı ve düzgün tanımlandı
class CommentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, file_id):
        file = get_object_or_404(GroupFile, id=file_id)
        text = request.data.get("text")
        comment = Comment.objects.create(file=file, user=request.user, text=text)
        handle_mentions(text, request.user)
        return Response(CommentSerializer(comment).data, status=201)

class CommentReplyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, comment_id):
        parent_comment = get_object_or_404(Comment, id=comment_id)
        text = request.data.get("text")
        reply = Comment.objects.create(
            file=parent_comment.file,
            user=request.user,
            text=text,
            parent=parent_comment
        )
        handle_mentions(text, request.user)
        return Response(CommentSerializer(reply).data, status=201)

# DÜZELTİLMİŞ: CommentListView - CommentReplyView dışına taşındı
class CommentListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        sort_by = request.query_params.get("sort", "new")  # "new" veya "top"
        file = get_object_or_404(GroupFile, id=file_id)

        if sort_by == "top":
            comments = Comment.objects.filter(file=file).annotate(
                like_count=Count("reactions", filter=Q(reactions__reaction_type="like"))
            ).order_by("-like_count", "-created_at")
        else:
            comments = Comment.objects.filter(file=file).order_by("-created_at")

        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

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

        def aggregate_by(interval):
            qs = (
                FileViewLog.objects.filter(file=file)
                .annotate(period=interval("viewed_at"))
                .values("period")
                .annotate(count=Count("id"))
                .order_by("period")
            )
            return list(qs)

        daily_stats = aggregate_by(TruncDate)
        weekly_stats = aggregate_by(TruncWeek)
        monthly_stats = aggregate_by(TruncMonth)

        return Response({
            "file": file.filename,
            "total_views": logs.count(),
            "logs": serializer.data,
            "stats": {
                "daily": daily_stats,
                "weekly": weekly_stats,
                "monthly": monthly_stats,
            }
        })

class FileReportExportCSV(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        file = get_object_or_404(GroupFile, id=file_id, uploaded_by=request.user)
        logs = FileViewLog.objects.filter(file=file).order_by("-viewed_at")

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{file.filename}_report.csv"'

        writer = csv.writer(response)
        writer.writerow(["Kullanıcı", "Tarih"])
        for log in logs:
            writer.writerow([log.user.username, log.viewed_at.strftime("%Y-%m-%d %H:%M:%S")])

        return response

class FileReportExportPDF(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        file = get_object_or_404(GroupFile, id=file_id, uploaded_by=request.user)
        logs = FileViewLog.objects.filter(file=file).order_by("-viewed_at")

        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        p.setFont("Helvetica", 12)
        p.drawString(100, 800, f"Rapor: {file.filename}")
        p.drawString(100, 780, f"Toplam görüntülenme: {logs.count()}")

        y = 750
        for log in logs:
            line = f"{log.user.username} - {log.viewed_at.strftime('%Y-%m-%d %H:%M:%S')}"
            p.drawString(100, y, line)
            y -= 20
            if y < 50:  # sayfa dolarsa yeni sayfa
                p.showPage()
                y = 800

        p.save()
        buffer.seek(0)

        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{file.filename}_report.pdf"'
        return response


from django.http import JsonResponse
from django.conf import settings

def websocket_debug(request):
    return JsonResponse({
        'status': 'WebSocket debug',
        'asgi_application': getattr(settings, 'ASGI_APPLICATION', 'Not set'),
        'channels_installed': 'channels' in getattr(settings, 'INSTALLED_APPS', []),
        'installed_apps': [app for app in getattr(settings, 'INSTALLED_APPS', []) if 'channels' in app],
        'server_mode': 'WSGI (Channels not active)'
    })