from .models import File, CloudGroup, GroupFile, FileComment, SecureLink, Device
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.base import ContentFile
from django.http import FileResponse, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes
import uuid  
from rest_framework import status
from django.contrib.auth.models import User
from .models import CloudGroup, GroupInvite, GroupMember
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import os
import mimetypes, os, uuid
from .serializers import FileSerializer, CloudGroupSerializer, GroupFileSerializer, FileCommentSerializer, GroupInviteSerializer
from .utils import add_watermark
import secrets
from django.utils import timezone
from datetime import timedelta
from .serializers import SecureLinkSerializer
from rest_framework.decorators import action
from .models import MediaFile
from .serializers import MediaFileSerializer
from django.views.decorators.http import require_http_methods
import json


class MediaFileViewSet(viewsets.ModelViewSet):
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(uploader=self.request.user)

    @action(detail=True, methods=["POST"])
    def consume(self, request, pk=None):
        media = self.get_object()
        user = request.user

        if media.single_view and user in media.consumed_by.all():
            return Response({"detail": "Bu medya tek gosterimlik ve zaten goruntulediniz."},
                            status=status.HTTP_403_FORBIDDEN)

        # Kullanıcıyı tüketenler listesine ekle
        if media.single_view:
            media.consumed_by.add(user)
            media.save()

        serializer = self.get_serializer(media)
        return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_secure_link(request, file_id):
    file = get_object_or_404(File, id=file_id, owner=request.user)
    expires_in = int(request.data.get("expires_in", 24))  # saat
    max_uses = int(request.data.get("max_uses", 1))

    link = SecureLink.objects.create(
        file=file,
        token=secrets.token_urlsafe(16),
        expires_at=timezone.now() + timedelta(hours=expires_in),
        max_uses=max_uses
    )
    return Response(SecureLinkSerializer(link).data)

@api_view(["GET"])
def download_with_token(request, token):
    link = get_object_or_404(SecureLink, token=token)
    if not link.is_valid():
        return HttpResponseForbidden("Link expired or max uses reached")
    link.used_count += 1
    link.save()
    return FileResponse(link.file.file.open("rb"), as_attachment=True)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_invite(request):
    group_id = request.data.get("group_id")
    email = request.data.get("email")

    try:
        group = CloudGroup.objects.get(id=group_id, owner=request.user)
    except CloudGroup.DoesNotExist:
        return Response({"error": "Group not found or you are not the owner"}, status=403)

    invite = GroupInvite.objects.create(group=group, email=email, invited_by=request.user)
    serializer = GroupInviteSerializer(invite)
    return Response(serializer.data, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept_invite(request):
    invite_id = request.data.get("invite_id")

    try:
        invite = GroupInvite.objects.get(id=invite_id, email=request.user.email, accepted=False)
    except GroupInvite.DoesNotExist:
        return Response({"error": "No pending invite found"}, status=404)

    # Kullanıcıyı gruba ekle
    GroupMember.objects.create(group=invite.group, user=request.user, role="member")
    invite.accepted = True
    invite.save()

    return Response({"message": f"Joined group {invite.group.name}"}, status=200)

@csrf_exempt
@require_http_methods(["POST"]) 
def kayit_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            
            # Kullanıcıyı oluştur
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Kullanici basariyla kaydedildi',
                'user_id': user.id
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Hata: {str(e)}'
            })

# User personal files
class FileUploadListView(generics.ListCreateAPIView):
    serializer_class = FileSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return File.objects.filter(owner=self.request.user).order_by('-uploaded_at')

    def perform_create(self, serializer):
        file_obj = self.request.data.get("file")
        instance = serializer.save(owner=self.request.user)

        mime_type, _ = mimetypes.guess_type(file_obj.name)
        if mime_type and mime_type.startswith("image"):
            # Önce instance'ı kaydet ki dosya yolu oluşsun
            instance.save()

            original_path = instance.file.path
            # Dosya uzantısını değiştirirken base_path kullan
            base_path = os.path.splitext(original_path)[0]
            watermarked_path = base_path + "_wm.jpg"

            try:
                add_watermark(original_path, watermarked_path, username=self.request.user.username)

                with open(watermarked_path, "rb") as f:
                    instance.file.save(os.path.basename(watermarked_path), ContentFile(f.read()), save=True)

                # Geçici dosyaları temizle
                if os.path.exists(original_path):
                    os.remove(original_path)
                if os.path.exists(watermarked_path):
                    os.remove(watermarked_path)
                    
            except Exception as e:
                # Hata durumunda işlemi iptal et
                instance.delete()
                raise serializers.ValidationError(f"Watermark eklenirken hata oluştu: {str(e)}")

        # Tek seferlik görüntüleme için token üret
        if instance.one_time_view:
            instance.view_token = str(uuid.uuid4())
            instance.viewed = False  # Görüntülenmedi olarak işaretle
            instance.save()

class FileDetailView(generics.RetrieveAPIView):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]

class FileOneTimeView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = FileSerializer
    
    @method_decorator(never_cache)
    def get(self, request, token):
        try:
            # Dosyayı token ile bul
            f = File.objects.get(view_token=token)
        except File.DoesNotExist:
            return Response({'detail': 'Invalid token'}, status=status.HTTP_404_NOT_FOUND)
        
        # Dosya zaten görüntülenmişse hata döndür
        if f.has_been_viewed:
            return Response({
                'detail': 'This file has already been viewed and is no longer available.'
            }, status=status.HTTP_410_GONE)
        
        # Dosyayı görüntülendi olarak işaretle
        f.has_been_viewed = True
        f.save()
        
        # Dosya yolunu al
        file_path = f.file.path
        
        try:
            # WITH bloğu içinde dosyayı aç ve oku
            with open(file_path, 'rb') as file:
                # İçerik türünü belirle
                content_type, encoding = mimetypes.guess_type(file_path)
                if content_type is None:
                    content_type = 'application/octet-stream'
                
                # Dosya içeriğini oku
                file_content = file.read()
                
                # Yanıt oluştur
                response = HttpResponse(file_content, content_type=content_type)
                response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
                
                # Önbellek önleyici başlıklar
                response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response['Pragma'] = 'no-cache'
                response['Expires'] = '0'
                
                return response
                
        except IOError as e:
            # Dosya okuma hatası
            return Response({
                'detail': f'File could not be opened: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            # Diğer beklenmeyen hatalar
            return Response({
                'detail': f'An unexpected error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Groups
class CloudGroupCreateView(generics.CreateAPIView):
    serializer_class = CloudGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        group = serializer.save(owner=self.request.user)
        group.members.add(self.request.user)

class CloudGroupJoinView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response({'detail':'token required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            group = CloudGroup.objects.get(invite_token=token)
        except CloudGroup.DoesNotExist:
            return Response({'detail':'invalid token'}, status=status.HTTP_404_NOT_FOUND)
        group.members.add(request.user)
        return Response({'detail':'joined'})

    # Grup listesi
class CloudGroupListView(generics.ListAPIView):
    serializer_class = CloudGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Kullanıcının üyesi olduğu grupları getir
        return CloudGroup.objects.filter(members=self.request.user)

# Grup detayı
class CloudGroupDetailView(generics.RetrieveAPIView):
    serializer_class = CloudGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = CloudGroup.objects.all()
    
    def get_object(self):
        # Kullanıcının gruba üye olup olmadığını kontrol et
        group = super().get_object()
        if self.request.user not in group.members.all():
            raise PermissionDenied('Bu gruba erisim izniniz yok')
        return group

# Grup detay görünümü

class GroupFileUploadView(generics.ListCreateAPIView):
    serializer_class = GroupFileSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        gid = self.kwargs.get('group_id')
        return GroupFile.objects.filter(group_id=gid).order_by('-uploaded_at')

    def perform_create(self, serializer):
        gid = self.kwargs.get('group_id')
        group = get_object_or_404(CloudGroup, pk=gid)
        if self.request.user not in group.members.all():
            raise PermissionDenied('not a member')
        file_obj = self.request.data.get('file')
        instance = serializer.save(group=group, uploader=self.request.user)
        mime_type, _ = mimetypes.guess_type(file_obj.name)
        if mime_type and mime_type.startswith("image"):
            original_path = instance.file.path
            watermarked_path = original_path.replace(os.path.splitext(original_path)[1], "_wm.jpg")
            add_watermark(original_path, watermarked_path, username=self.request.user.username)
            with open(watermarked_path, "rb") as f:
                instance.file.save(os.path.basename(watermarked_path), ContentFile(f.read()), save=True)
            try:
                os.remove(original_path)
                os.remove(watermarked_path)
            except:
                pass
        if instance.one_time_view:
            instance.view_token = uuid.uuid4()
            instance.save()

class GroupFileCommentCreateView(generics.CreateAPIView):
    serializer_class = FileCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        file_id = self.kwargs.get('file_id')
        gf = get_object_or_404(GroupFile, pk=file_id)
        group = gf.group
        if self.request.user not in group.members.all():
            raise PermissionDenied('not a member')
        serializer.save(author=self.request.user, file=gf)

def range_download_view(request, file_name):
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)

    if not os.path.exists(file_path):
        return HttpResponse("Dosya bulunamadı", status=404)

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get('Range', None)

    if range_header:
        # Örn: "bytes=1000-"
        start, end = range_header.replace("bytes=", "").split("-")
        start = int(start) if start else 0
        end = int(end) if end else file_size - 1
        length = end - start + 1

        with open(file_path, 'rb') as f:
            f.seek(start)
            data = f.read(length)

        response = HttpResponse(data, status=206, content_type="application/octet-stream")
        response['Content-Range'] = f"bytes {start}-{end}/{file_size}"
        response['Accept-Ranges'] = "bytes"
        response['Content-Length'] = str(length)
        return response

    # Eğer Range yoksa dosyanın tamamını gönder
    return FileResponse(open(file_path, 'rb'), as_attachment=True)

# register_device ve access_file fonksiyonlarını en dış seviyeye taşıyın
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_device(request):
    """
    Kullanici cihazini kaydeder. Cihaz UUID ve opsiyonel isim gonderilir.
    """
    device_uuid = request.data.get("device_uuid")
    device_name = request.data.get("device_name", "")
    if not device_uuid:
        return Response({"error": "device_uuid gerekli"}, status=400)

    try:
        device_uuid_obj = uuid.UUID(device_uuid)
    except ValueError:
        return Response({"error": "gecersiz UUID"}, status=400)

    device, created = Device.objects.get_or_create(
        user=request.user,
        device_uuid=device_uuid_obj,
        defaults={"device_name": device_name}
    )

    return Response({
        "device_id": str(device.device_uuid),
        "device_name": device.device_name,
        "registered": created
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def access_file(request, file_name):
    """
    Cihaz dogrulamasi yapar ve dosya erisimi verir.
    Cihaz UUID header veya query param ile gonderilir.
    """
    device_uuid = request.headers.get("X-Device-UUID") or request.query_params.get("device_uuid")
    if not device_uuid:
        return Response({"error": "device_uuid gerekli"}, status=400)

    try:
        device_uuid_obj = uuid.UUID(device_uuid)
    except ValueError:
        return Response({"error": "gecersiz UUID"}, status=400)

    if not Device.objects.filter(user=request.user, device_uuid=device_uuid_obj).exists():
        return Response({"error": "cihaz dogurulmasi basarisiz"}, status=403)

    # Dosya yolunu ayarla
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)
    if not os.path.exists(file_path):
        return HttpResponse("Dosya bulunamadi", status=404)

@csrf_exempt
@require_POST
def login_view(request):
    try:
        data = json.loads(request.body)
        # Giriş işlemleri...
        return JsonResponse({'user': {'email': data['email']}})
    except Exception as e:
        return JsonResponse({'detail': str(e)}, status=400)

@csrf_exempt
@require_POST
def signup_view(request):
    try:
        data = json.loads(request.body)
        # Kayıt işlemleri...
        return JsonResponse({'user': {'email': data['email']}})
    except Exception as e:
        return JsonResponse({'detail': str(e)}, status=400)

    return FileResponse(open(file_path, "rb"), as_attachment=True)
pass

