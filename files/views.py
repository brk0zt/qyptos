# -*- coding: utf-8 -*-
from django.shortcuts import render
import logging
from django.http import HttpResponse
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from .models import File, CloudGroup, GroupFile, FileComment, SecureLink
from users.models import Device
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.base import ContentFile
from django.http import FileResponse, HttpResponse, JsonResponse, HttpResponseForbidden, HttpResponseGone
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.cache import never_cache
from django.utils.decorators import method_decorator
from rest_framework.decorators import api_view, permission_classes
from django.core.files.storage import default_storage
import uuid  
from django.contrib.auth.models import User
from .models import CloudGroup, GroupInvite, GroupMember
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import os
import mimetypes
from .serializers import FileSerializer, CloudGroupSerializer, GroupFileSerializer, FileCommentSerializer, GroupInviteSerializer, FileShareSerializer  
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
from rest_framework.permissions import AllowAny
from .models import FileShare
from django.db.models import Count, Q, F, ExpressionWrapper, FloatField
from django.db.models.functions import Coalesce
from memory.services.advanced_memory_manager import AdvancedMemoryManager
from memory.models import MemoryItem
from rest_framework import generics, mixins
import base64
import numpy as np
import cv2
from django.db import models
import mimetypes
from django.core.cache import cache
import time
from PIL import Image
from users.security.camera_detector import security_detector 

logger = logging.getLogger(__name__)

# OpenCV fallback mekanizması
try:
    import cv2
    OPENCV_AVAILABLE = True
    logger.info("OpenCV başarıyla yüklendi")
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV yüklenemedi, Pillow kullanılacak")


def share_file_view(request, token):
    # Token'ı yakala
    try:
        share = FileShare.objects.get(token=token)
    except FileShare.DoesNotExist:
        # 404 sayfasına yönlendir veya hata mesajı döndür
        return render(request, 'index.html', {'error': 'Paylaşım bulunamadi.'})

    # DOSYA KONTROLÜ
    is_consumed_by_backend = not share.is_valid()
    
    # --- KRİTİK HATA AYIKLAMA KODU ---
    if not share.is_valid():
        print("------------------------------------------")
        print("HATA AYIKLAMA: DOSYA GEÇERSİZ SAYILIYOR")
        print(f"Token: {token}")
        print(f"is_expired: {share.is_expired()}")  # TRUE ise neden süresi dolduğunu kontrol et.
        print(f"is_revoked: {share.is_revoked}")    # TRUE ise admin panelinden kontrol et.
        print(f"view_count: {share.view_count}, max_views: {share.max_views}") 
        print("------------------------------------------")
        # Eğer view_count hala 0 ise, sorun is_expired() veya is_revoked'dadır.
        
    # ... devam eden kısım (React'e JSON data yollanan yer)
    
    # is_consumed_by_backend değerini React componentine gönder
    context = {
        # ... diğer context değişkenleri
        'is_consumed_by_backend': is_consumed_by_backend,
        # ...
    }
    return render(request, 'frontend/build/index.html', context)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_file(request):
    """Dosya yükleme endpoint'i - OpenCV/Pillow uyumlu"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'Dosya bulunamadı'}, status=400)
        
        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name
        
        # Dosya bilgilerini al
        file_size = uploaded_file.size
        
        # Görsel dosyaları için boyut bilgisi
        width, height = None, None
        file_type = uploaded_file.content_type or 'unknown'
        
        if file_type.startswith('image/'):
            try:
                if OPENCV_AVAILABLE:
                    # OpenCV ile işle
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                        for chunk in uploaded_file.chunks():
                            tmp_file.write(chunk)
                        tmp_file.flush()
                        
                        image = cv2.imread(tmp_file.name)
                        if image is not None:
                            height, width = image.shape[:2]
                        os.unlink(tmp_file.name)
                else:
                    # Pillow ile işle
                    image = Image.open(uploaded_file)
                    width, height = image.size
                    
            except Exception as e:
                logger.warning(f"Görsel boyutu alınamadı: {e}")
        
        # Dosyayı kaydet
        uploaded_file.seek(0)  # Reset file pointer
        file_path = default_storage.save(file_name, ContentFile(uploaded_file.read()))
        
        # Memory sistemine kaydet (opsiyonel)
        try:
            from memory.services.advanced_memory_manager import AdvancedMemoryManager
            memory_manager = AdvancedMemoryManager(request.user)
            # Memory item oluşturma işlemi burada yapılabilir
        except Exception as e:
            logger.warning(f"Memory kaydı oluşturulamadı: {e}")
        
        response_data = {
            'message': 'Dosya başarıyla yüklendi',
            'file_path': file_path,
            'file_name': file_name,
            'file_size': file_size,
            'file_type': file_type,
        }
        
        if width and height:
            response_data['dimensions'] = {'width': width, 'height': height}
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Dosya yükleme hatası: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny])
def secure_file_view(request, token):
    """
    Tek kullanımlık veya token tabanlı dosyaları sunar ve görüntüleme sayacını artırır.
    """
    try:
        # Token ile FileShare nesnesini al ve iptal edilmemiş olduğunu kontrol et
        share = FileShare.objects.get(token=token, is_revoked=False)
    except FileShare.DoesNotExist:
        return HttpResponseForbidden("Erisim reddedildi.") 

    # 1. Süre ve Maksimum Görüntüleme Kontrolleri
    if share.is_expired():
        return HttpResponseGone("Bu paylasim suresi doldu.")
    
    if share.view_count >= share.max_views:
        # Maksimum görüntüleme sayısına ulaşıldıysa, 410 döndür.
        return HttpResponseGone("Maksimum görüntüleme sayisina ulasildi.")

    # 2. Dosya Erişimi
    try:
        # Tüketim başarılı olursa (yani dosya indirilirse) sayacı artır
        share.view_count += 1 # 🚨 SAYACI BURADA ARTIRIYORUZ 🚨
        share.save()
        
        file_object = share.file.file
        file_path = file_object.path
    except Exception:
        return HttpResponseGone("Dosya içeriği bulunamadi.")
    
    # 4. Dosyayı Güvenlik Başlıkları ile Gönderme
    content_type = file_object.file.content_type if hasattr(file_object.file, 'content_type') else 'application/octet-stream'

    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    
    # Content-Disposition: 'inline' görsellerin tarayıcıda açılmasını sağlar.
    response['Content-Disposition'] = f'inline; filename="{file_object.name}"'
    
    # Önemli Başlıklar: Tarayıcıların önbelleklemesini, kaydetmesini ve MIME tahminini engeller.
    response['Content-Disposition'] = f'inline; filename="{file_object.name}"'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['X-Content-Type-Options'] = 'nosniff'

    return response

@require_POST
def stop_camera_monitoring(request):
    security_detector.stop_monitoring() # camera_detector.py'daki thread durdurma fonksiyonu
    # Başarılı yanıt
    return JsonResponse({"status": "ok", "message": "Camera monitoring stopped."}, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_files(request):
    """Kullanıcının dosyalarını listele"""
    try:
        # Basit dosya listesi - gerçek uygulamada database'den alınmalı
        files = []
        return JsonResponse({'files': files})
    except Exception as e:
        logger.error(f"Dosya listeleme hatası: {e}")
        return JsonResponse({'error': str(e)}, status=500)

def get_client_ip(request):
    """İstemci IP adresini al"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class MediaFileViewSet(viewsets.ModelViewSet):
    queryset = MediaFile.objects.all()
    serializer_class = MediaFileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        file_obj = self.request.data.get("file")
        instance = serializer.save(uploader=self.request.user)

        mime_type, _ = mimetypes.guess_type(file_obj.name)
        if mime_type and mime_type.startswith("image"):
            try:
                instance.save()
                original_path = instance.file.path
                base_path = os.path.splitext(original_path)[0]
                watermarked_path = base_path + "_wm.jpg"

                add_watermark(original_path, watermarked_path, username=self.request.user.username)

                with open(watermarked_path, "rb") as f:
                    instance.file.save(os.path.basename(watermarked_path), ContentFile(f.read()), save=True)

                if os.path.exists(original_path):
                    os.remove(original_path)
                if os.path.exists(watermarked_path):
                    os.remove(watermarked_path)
                    
            except Exception as e:
                print(f"Watermark hatasi: {str(e)}")
                pass

        if instance.single_view:
            pass

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_secure_link(request, file_id):
    file = get_object_or_404(File, id=file_id, owner=request.user)
    expires_in = int(request.data.get("expires_in", 24))
    max_uses = int(request.data.get("max_uses", 1))

    link = SecureLink.objects.create(
        file=file,
        token=secrets.token_urlsafe(16),
        expires_at=timezone.now() + timedelta(hours=expires_in),
        max_uses=max_uses
    )
    return Response(SecureLinkSerializer(link).data)

@api_view(["GET"])
@permission_classes([AllowAny])
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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_camera_frame(request):
    """Frontend'den gelen frame'i analiz et"""
    try:
        frame_file = request.FILES.get('frame')
        if not frame_file:
            return Response({'error': 'Frame bulunamadı'}, status=400)
        
        # Frame'i OpenCV formatına çevir
        file_bytes = np.frombuffer(frame_file.read(), np.uint8)
        frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if frame is None:
            return Response({'error': 'Frame decode edilemedi'}, status=400)
        
        # Güvenlik analizi yap
        from users.security.camera_detector import security_detector
        
        security_status = security_detector.monitor_security(frame)
        
        return Response({
            'security_breach': security_status == "BLOCK_SCREEN",
            'reason': 'CAMERA_DETECTED' if security_status == "BLOCK_SCREEN" else 'CLEAR',
            'face_detected': security_detector.detect_faces(frame),
            'lens_detected': security_detector.multi_method_lens_detection(frame)
        })
        
    except Exception as e:
        print(f"Frame analiz hatası: {str(e)}")
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def report_security_breach(request):
    """Frontend'den gelen güvenlik ihlalini kaydet"""
    try:
        data = request.data
        user = request.user
        
        # Güvenlik ihlalini logla
        print(f"GÜVENLİK İHLALİ - Kullanıcı: {user.username}, Sebep: {data.get('reason')}")
        
        #SecurityBreach.objects.create(user=user, reason=data.get('reason'))
        
        return Response({'status': 'reported'})
        
    except Exception as e:
        print(f"Güvenlik ihlali raporlama hatası: {str(e)}")
        return Response({'error': str(e)}, status=500)

class SecureMediaView(APIView):
    """Güvenli medya görüntüleme view'ı"""
    permission_classes = [AllowAny]
    
    def get(self, request, token):
        try:
            # Önce güvenlik kontrolü yap
            security_check = self.check_security(request)
            if not security_check['allowed']:
                return self.render_security_block(security_check['reason'])
            
            # Normal medya görüntüleme işlemi
            return self.render_media(token)
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)

    def render_media(self, token):
        """Medya dosyasını token ile döndürme mantığı burada olmalı"""
        
        # Örnek bir placeholder veya gerçek dosya döndürme mantığı
        file_share = get_object_or_404(FileShare, token=token)
        return FileResponse(file_share.file.file.path)
        
        return HttpResponse("Render media metodu henüz uygulanmadı.", status=200)
    
    def check_security(self, request):
        """Güvenlik kontrollerini yap"""
        from users.security.camera_detector import security_detector
        
        # Backend kamera kontrolü (opsiyonel)
        backend_breach = security_detector.security_breach
        
        return {
            'allowed': not backend_breach,
            'reason': 'BACKEND_CAMERA_DETECTED' if backend_breach else 'CLEAR'
        }
    
    def render_security_block(self, reason):
        """Güvenlik engeli sayfası render et"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Güvenlik Uyarısı</title>
            <style>
                body {{ 
                    background: black; 
                    color: white; 
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 50px;
                }}
                .warning {{
                    background: #ff4444;
                    padding: 30px;
                    border-radius: 10px;
                    margin: 20px auto;
                    max-width: 500px;
                }}
            </style>
        </head>
        <body>
            <div class="warning">
                <h1>🚨 GÜVENLİK İHLALİ TESPİT EDİLDİ</h1>
                <p>Bu içerik güvenlik nedeniyle engellendi.</p>
                <p><strong>Sebep:</strong> {reason}</p>
                <p>Lütfen kayıt cihazlarını kapatıp sayfayı yenileyin.</p>
            </div>
        </body>
        </html>
        """
        return HttpResponse(html_content)


# files/views.py

@api_view(['GET'])
@permission_classes([AllowAny])
def secure_media_view(request, token):
    """Güvenli medya dosyasını sunar ve Tüketimi yapar."""
    file_obj = None
    file_share = None

    try:
        # 1. FileShare'de ara
        try:
            file_share = FileShare.objects.select_related('file').get(
                token=token,
                is_revoked=False
            )
            file_obj = file_share.file
        except FileShare.DoesNotExist:
            # FileShare yoksa, File'da view_token ile aramaya devam et
            try:
                file_obj = File.objects.get(view_token=token)
            except File.DoesNotExist:
                return Response({"error": "Geçersiz token"}, status=404)

        # 2. Tüketim kontrolü
        is_already_consumed = False
        if file_share:
            if file_share.view_count >= file_share.max_views:
                is_already_consumed = True
        elif file_obj and file_obj.one_time_view and file_obj.has_been_viewed:
            is_already_consumed = True

        if is_already_consumed:
            return Response({"error": "Bu medya zaten tüketildi."}, status=410)

        # 3. Dosya Yolunu Kontrol Et
        if not file_obj or not file_obj.file:
             return Response({"error": "Dosya bulunamadı"}, status=404)

        file_path = file_obj.file.path
        if not os.path.exists(file_path):
            return Response({"error": "Dosya diskte bulunamadı"}, status=404)

        # 4. Content-Type belirleme
        content_type, encoding = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'

        # 5. TÜKETİM MANTIĞI (Önce veritabanını güncelle)
        if file_share:
            file_share.view_count += 1
            file_share.save()
        elif file_obj and file_obj.one_time_view and not file_obj.has_been_viewed:
            file_obj.has_been_viewed = True
            file_obj.save()

        # 6. Dosyayı Sun (Response burada oluşturulmalı)
        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type
        )

        # 7. Güvenlik ve önbellek ayarları
        filename = os.path.basename(file_path)
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        # Bu headerlar tarayıcının kaydetmesini engeller
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        response['X-Content-Type-Options'] = 'nosniff'

        return response

    except Exception as e:
        print(f"Secure media error: {str(e)}")
        return Response({"error": "Dosya sunulurken hata oluştu"}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_files(request):
    """Debug endpoint to check file data"""
    try:
        files = File.objects.filter(owner=request.user)
        data = []
        for file in files:
            data.append({
                'id': file.id,
                'name': file.file.name if file.file else None,
                'path': file.file.path if file.file else None,
                'url': file.file.url if file.file else None,
                'size': file.file_size,
                'exists': os.path.exists(file.file.path) if file.file else False
            })
        return Response(data)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

class FileUploadListView(mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView):
    serializer_class = FileSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            qs = File.objects.filter(owner=self.request.user).order_by('-uploaded_at')
            print(f"📁 File count: {qs.count()}")
            for f in qs:
                print(f"🧾 File ID: {f.id}, name: {f.file.name if f.file else 'None'}")
                try:
                    print(f"   URL: {f.file.url}")
                    print(f"   PATH: {f.file.path}")
                except Exception as e:
                    print(f"   ❌ HATA - Bu dosya bozuk olabilir: {e}")
            return qs
        except Exception as e:
            print(f"Get queryset error: {str(e)}")
            return File.objects.none()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        try:
            print("File upload basliyor...")
            return super().create(request, *args, **kwargs)
        except Exception as e:
            print(f"File upload error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Dosya yuklenirken hata olustu: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
        try:
            file_obj = self.request.data.get("file")
            if not file_obj:
                raise serializers.ValidationError("Dosya secilmedi")
            
            print(f"Dosya adi: {file_obj.name}, Boyut: {file_obj.size}")
            
            view_duration = self.request.data.get("view_duration", "unlimited")

            # Hata Düzeltme: String olarak gelen 'false' veya 'true' değerlerini Python boolean'ına çevirme
            # is_public ve one_time_view, form verisi olarak string geldiyse dönüştürülmelidir.

            # 'true', 't', '1', 'on' gibi değerler True kabul edilir, diğerleri (varsayılan değer dahil) False kabul edilir.
            one_time_view = str(self.request.data.get("one_time_view", "False")).lower() in ('true', 't', '1', 'on')
            is_public = str(self.request.data.get("is_public", "False")).lower() in ('true', 't', '1', 'on')
            
            instance = serializer.save(
                owner=self.request.user, 
                file_size=file_obj.size,
                view_duration=view_duration,
                one_time_view=one_time_view,
                is_public=is_public
            )

            mime_type, _ = mimetypes.guess_type(file_obj.name)
            print(f"File MIME type: {mime_type}")
            
            if mime_type and mime_type.startswith("image"):
                try:
                    # Save first to get the file path
                    instance.save()
                    original_path = instance.file.path
                    print(f"Original path: {original_path}")
                    
                    if os.path.exists(original_path):
                        base_path = os.path.splitext(original_path)[0]
                        watermarked_path = base_path + "_wm.jpg"
                        print(f"Watermarked path: {watermarked_path}")

                        add_watermark(original_path, watermarked_path, username=self.request.user.username)

                        with open(watermarked_path, "rb") as f:
                            instance.file.save(
                                os.path.basename(watermarked_path), 
                                ContentFile(f.read()), 
                                save=True
                            )

                        # Clean up temporary files
                        if os.path.exists(original_path):
                            os.remove(original_path)
                        if os.path.exists(watermarked_path):
                            os.remove(watermarked_path)
                    else:
                        print("Original dosya path'i bulunamadi")
                        
                except Exception as e:
                    print(f"Watermark error: {str(e)}")
                    # Don't delete the instance if watermark fails, just continue without watermark
            
            if instance.one_time_view:
                instance.view_token = str(uuid.uuid4())
                instance.has_been_viewed = False
                instance.save()

            print(f"File uploaded successfully: {instance.file.name}")
            
        except Exception as e:
            print(f"Perform create error: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Ekran koruma endpoint'lerinde özel header kontrolü
        if '/share/' in request.path:
            # Şüpheli istekleri tespit et
            user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
            suspicious_agents = ['bot', 'crawler', 'scraper', 'screenshot']
            
            if any(agent in user_agent for agent in suspicious_agents):
                return JsonResponse(
                    {'error': 'Güvenlik ihlali tespit edildi'}, 
                    status=403
                )
        
        response = self.get_response(request)
        return response

def consume_file(request, file_id):
        if request.method == 'POST':
            file_obj = get_object_or_404(File, id=file_id)
        
            if not file_obj.one_time_view:
                return JsonResponse({'detail': 'Bu dosya tek gösterimlik değil.'}, status=400)
            
            if file_obj.is_consumed:
                return JsonResponse({'detail': 'Bu dosya zaten tüketildi.'}, status=410)
            
        # Sadece bu POST isteği gelince tüketildi olarak işaretle
            file_obj.is_consumed = True
            file_obj.save()
        
        # Dosyayı sunucudan silmek isterseniz:
            file_obj.file.delete()
        
            return JsonResponse({'detail': 'Dosya başarıyla tüketildi.'}, status=200)
    
        return JsonResponse({'detail': 'Sadece POST metoduna izin verilir.'}, status=405)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_file(request, file_id):
    file_obj = get_object_or_404(File, id=file_id)

    if file_obj.one_time_view and file_obj.is_consumed:
        # Zaten tüketilmişse 410 döndür.
        return HttpResponseGone('{"detail": "Bu dosya zaten görüntülendi ve artık kullanılamaz."}', 
                                content_type='application/json')

    file_path = file_obj.file.path
    if not os.path.exists(file_path):    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("Range", "").strip()

    if range_header:
        # Örn: "bytes=0-1023"
        range_value = range_header.split("=")[1]
        start, end = range_value.split("-")
        start = int(start)
        end = int(end) if end else file_size - 1
        length = end - start + 1

        with open(file_path, "rb") as f:
            f.seek(start)
            data = f.read(length)

        response = HttpResponse(data, status=206, content_type="application/octet-stream")
        response["Content-Range"] = f"bytes {start}-{end}/{file_size}"
        response["Accept-Ranges"] = "bytes"
        response["Content-Length"] = str(length)
        response = FileResponse(open(file_path, 'rb'), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_obj.filename}"'
        return response

    else:
        # Normal indirme (tam dosya)
        response = FileResponse(open(file_path, "rb"), as_attachment=True, filename=os.path.basename(file_path))
        response["Accept-Ranges"] = "bytes"
        return response

def render_secure_html_page(request, file_obj):
    """Güvenli HTML sayfası oluştur"""
    
    # Dosya URL'sini oluştur
    file_url = request.build_absolute_uri(file_obj.file.url)
    
    # Dosya türünü belirle
    file_name = file_obj.file.name.lower()
    is_video = any(file_name.endswith(ext) for ext in ['.mp4', '.avi', '.mov', '.mkv'])
    is_image = any(file_name.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp'])
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Güvenli Görüntüleyici - {file_obj.file.name}</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: #0a0a0a;
                color: white;
                font-family: Arial, sans-serif;
                overflow: hidden;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
            }}
            
            .secure-container {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                background: #000;
            }}
            
            .media-container {{
                max-width: 95%;
                max-height: 80vh;
                position: relative;
                border: 3px solid #ff4444;
                border-radius: 8px;
                overflow: hidden;
                background: #000;
            }}
            
            .media-container img,
            .media-container video {{
                max-width: 100%;
                max-height: 80vh;
                display: block;
            }}
            
            .protection-overlay {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                background: repeating-linear-gradient(
                    45deg,
                    transparent,
                    transparent 10px,
                    rgba(255, 0, 0, 0.02) 10px,
                    rgba(255, 0, 0, 0.02) 20px
                );
                z-index: 9998;
            }}
            
            .watermark {{
                position: absolute;
                bottom: 10px;
                right: 10px;
                color: rgba(255, 255, 255, 0.3);
                font-size: 12px;
                background: rgba(0, 0, 0, 0.5);
                padding: 5px 10px;
                border-radius: 3px;
                pointer-events: none;
                z-index: 9999;
            }}
            
            .header {{
                position: absolute;
                top: 20px;
                left: 0;
                width: 100%;
                text-align: center;
                color: #ff4444;
                font-weight: bold;
                z-index: 10000;
            }}
            
            @keyframes shake {{
                0%, 100% {{ transform: translateX(0); }}
                25% {{ transform: translateX(-10px); }}
                75% {{ transform: translateX(10px); }}
            }}
            
            .shake {{
                animation: shake 0.5s;
            }}
        </style>
    </head>
    <body>
        <div class="secure-container">
            <div class="header">
                🔒 GÜVENLİ GÖRÜNTÜLEYİCİ - EKRAN GÖRÜNTÜSÜ ALINAMAZ
            </div>
            
            <div class="media-container" id="mediaContainer">
                {"<video controls src='" + file_url + "'></video>" if is_video else "<img src='" + file_url + "' alt='Güvenli içerik'>"}
                <div class="protection-overlay"></div>
                <div class="watermark" id="watermark">
                    {file_obj.owner.username if file_obj.owner else 'Kullanıcı'} | {timezone.now().strftime('%d.%m.%Y %H:%M')}
                </div>
            </div>
        </div>

        <script>
            // GÜÇLÜ KORUMA SİSTEMİ
            let violationCount = 0;
            const maxViolations = 2;
            
            // Tuş yakalama
            document.addEventListener('keydown', function(e) {{
                const screenshotKeys = [
                    'PrintScreen', 'Snapshot', 'F13', 'F14', 'F15'
                ];
                
                const screenshotCombos = [
                    {{ ctrl: true, key: 'p' }},
                    {{ meta: true, shift: true, key: '3' }},
                    {{ meta: true, shift: true, key: '4' }},
                    {{ meta: true, shift: true, key: '5' }},
                    {{ ctrl: true, shift: true, key: 'p' }}
                ];
                
                // Tek tuşları engelle
                if (screenshotKeys.includes(e.key)) {{
                    blockScreenshot(e);
                    return;
                }}
                
                // Kombinasyonları engelle
                for (const combo of screenshotCombos) {{
                    if (e.key.toLowerCase() === combo.key && 
                        !!e.ctrlKey === !!combo.ctrl &&
                        !!e.metaKey === !!combo.meta && 
                        !!e.shiftKey === !!combo.shift) {{
                        blockScreenshot(e);
                        return;
                    }}
                }}
            }}, true);
            
            // Sağ tık engelleme
            document.addEventListener('contextmenu', function(e) {{
                e.preventDefault();
                showAlert('🚫 Sağ tık devre dışı bırakıldı!');
                return false;
            }}, true);
            
            // Kopyalama engelleme
            document.addEventListener('copy', function(e) {{
                e.preventDefault();
                return false;
            }}, true);
            
            // Görünürlük değişikliği
            document.addEventListener('visibilitychange', function() {{
                if (document.hidden) {{
                    violationCount++;
                    showAlert('🚨 Sayfa gizlendi! Güvenlik ihlali tespit edildi.');
                    checkViolations();
                }}
            }});
            
            // Ekran koruma fonksiyonları
            function blockScreenshot(e) {{
                e.preventDefault();
                e.stopPropagation();
                
                // Sayfayı titret
                document.body.classList.add('shake');
                setTimeout(() => {{
                    document.body.classList.remove('shake');
                }}, 500);
                
                violationCount++;
                showAlert('🚫 EKRAN GÖRÜNTÜSÜ ALINAMAZ!\\n\\nGüvenlik ihlali tespit edildi.');
                checkViolations();
            }}
            
            function showAlert(message) {{
                // Basit alert yerine modal göster
                const alertDiv = document.createElement('div');
                alertDiv.style.cssText = `
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: rgba(255, 0, 0, 0.9);
                    color: white;
                    padding: 20px;
                    border-radius: 8px;
                    z-index: 100000;
                    font-family: Arial;
                    text-align: center;
                    border: 2px solid white;
                    box-shadow: 0 0 30px rgba(255, 0, 0, 0.5);
                `;
                alertDiv.innerHTML = `<div style="font-size: 48px; margin-bottom: 10px;">🚫</div><div>${{message}}</div>`;
                document.body.appendChild(alertDiv);
                
                setTimeout(() => {{
                    if (alertDiv.parentNode) {{
                        alertDiv.parentNode.removeChild(alertDiv);
                    }}
                }}, 3000);
            }}
            
            function checkViolations() {{
                if (violationCount >= maxViolations) {{
                    // İçeriği tamamen engelle
                    document.body.innerHTML = `
                        <div style="
                            width: 100vw; 
                            height: 100vh; 
                            background: black; 
                            color: red; 
                            display: flex; 
                            align-items: center; 
                            justify-content: center; 
                            flex-direction: column;
                            font-family: Arial;
                            text-align: center;
                        ">
                            <div style="font-size: 48px; margin-bottom: 20px;">🚫</div>
                            <h1>GÜVENLİK İHLALİ</h1>
                            <p>Bu içerik güvenlik nedeniyle kalıcı olarak engellendi.</p>
                            <p>Çok sayıda ekran görüntüsü girişimi tespit edildi.</p>
                        </div>
                    `;
                }}
            }}
            
            // Sayfa yüklendiğinde korumayı başlat
            console.log('🛡️ Güvenli Görüntüleyici Aktif!');
        </script>
    </body>
    </html>
    """
    
    return HttpResponse(html_content)

def serve_file_directly(file_obj):
    """Ortak dosya sunma fonksiyonu"""
    try:
        if not file_obj or not file_obj.file:
            print("❌ File object or file field is missing")
            return Response({"error": "Dosya objesi bulunamadı"}, status=status.HTTP_404_NOT_FOUND)

        file_path = file_obj.file.path
        print(f"✅ Serving file: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found on disk: {file_path}")
            return Response({"error": "Dosya diskte bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
        
        # Content-Type belirleme
        content_type, encoding = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'
        
        # FileResponse ile dosyayı sun
        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type,
            as_attachment=False  # Tarayıcıda göster
        )
        
        # Güvenlik ve önbellek ayarları
        filename = os.path.basename(file_path)
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        print(f"✅ File served successfully: {filename}")
        return response
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return Response({"error": "Dosya diskte bulunamadı"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return Response(
            {"error": f"Dosya sunulurken hata oluştu: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_share(request, share_id):
    share = get_object_or_404(FileShare, id=share_id, created_by=request.user)
    
    # DÜZELTME: share.delete() yerine is_revoked'ı True yap.
    share.is_revoked = True
    share.save() 
    
    return Response({"message": "Paylasim iptal edildi ve pasif hale getirildi."})

class FilePreviewView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        try:
            file_id = kwargs.get('pk')
            file_obj = get_object_or_404(File, id=file_id, owner=request.user)
            
            if not file_obj.file:
                return Response({"error": "Dosya bulunamadi"}, status=404)
            
            file_name = file_obj.file.name.lower()
            if not any(file_name.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
                return Response({"error": "Preview sadece gorseller icin kullanilabilir"}, status=400)
            
            response = FileResponse(file_obj.file.open('rb'), content_type='image/jpeg')
            response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_obj.file.name)}"'
            return response
        except Exception as e:
            print(f"Preview error: {str(e)}")
            return Response({"error": f"Dosya acilamadi: {str(e)}"}, status=500)

class FileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return File.objects.filter(owner=self.request.user)

    def perform_destroy(self, instance):
        if instance.file:
            if os.path.isfile(instance.file.path):
                os.remove(instance.file.path)
        instance.delete()

class FileOneTimeView(generics.RetrieveAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = FileSerializer
    
    @method_decorator(never_cache)
    def get(self, request, token):
        try:
            file_obj = File.objects.get(view_token=token)
            # DEBUG: Dosya bulundu, yolu konsola yazdır
            print(f"✅ Dosya bulundu, Token: {token}. Dosya Yolu: {file_obj.file.path}") 
        except File.DoesNotExist:
            # DEBUG: Neden 404 aldığımızı terminalde görelim
            print(f"❌ HATA: Token ile iliskili Dosya bulunamadi: {token}") 
            return Response({'detail': 'Gecersiz veya Suresi Dolan Dosya'}, status=status.HTTP_404_NOT_FOUND)
        
        # 1. Kontrol: Daha once goruntulenmis mi?
        if file_obj.one_time_view and file_obj.has_been_viewed:
            return Response({
                'detail': 'Bu dosya zaten goruntulendi ve artik kullanilamaz.'
            }, status=status.HTTP_410_GONE)

        # 3. Dosyayı FileResponse ile güvenli bir şekilde sun
        file_path = file_obj.file.path
        
        try:
            # Dosyayı FileResponse ile aç ve sun.
            response = FileResponse(open(file_path, 'rb'))
            
            # Content Type belirleme
            content_type, encoding = mimetypes.guess_type(file_path)
            response['Content-Type'] = content_type or 'application/octet-stream'

            # Güvenlik ve Önbellek Ayarları
            response['Content-Disposition'] = f'inline; filename="{file_obj.file.name.split("/")[-1]}"'
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            
            return response
        
        except FileNotFoundError:
            # Dosya diskte yoksa 404 döndür
            print(f"❌ KRITIK HATA: Dosya diskte bulunamadi: {file_path}")
            return Response({'detail': 'Dosya diskte bulunamadi.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Diğer hatalarda 500 döndür
            print(f"❌ BEKLENMEYEN HATA: Dosya sunulurken hata: {e}")
            return Response({'detail': 'Dosya sunumu sirasinda beklenmeyen bir hata olustu.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FileShareViewSet(viewsets.ModelViewSet):
    serializer_class = FileShareSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return FileShare.objects.filter(created_by=self.request.user)
    
    def perform_create(self, serializer):
        file_id = self.request.data.get('file')
        file = get_object_or_404(File, id=file_id, owner=self.request.user)
        share = serializer.save(created_by=self.request.user, file=file)

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

class CloudGroupListView(generics.ListAPIView):
    serializer_class = CloudGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CloudGroup.objects.filter(members=self.request.user)

class CloudGroupDetailView(generics.RetrieveAPIView):
    serializer_class = CloudGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = CloudGroup.objects.all()
    
    def get_object(self):
        group = super().get_object()
        if self.request.user not in group.members.all():
            raise PermissionDenied('Bu gruba erisim izniniz yok')
        return group

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
        return HttpResponse("Dosya bulunamadi", status=404)

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get('Range', None)

    if range_header:
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

    return FileResponse(open(file_path, 'rb'), as_attachment=True)

class TrendingAlgorithm:
    @staticmethod
    def calculate_trend_score(file_share):
        try:
            view_weight = (file_share.view_count / max(file_share.max_views, 1)) * 0.4
            
            time_elapsed = (timezone.now() - file_share.created_at).total_seconds()
            time_weight = max(0, 1 - (time_elapsed / 604800)) * 0.3
            
            recent_views = FileShare.objects.filter(
                id=file_share.id,
                created_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            engagement_weight = (recent_views / max(file_share.view_count, 1)) * 0.2
            
            momentum = min(1.0, file_share.view_count / 100) * 0.1 if file_share.view_count > 10 else 0
            
            total_score = (view_weight + time_weight + engagement_weight + momentum) * 100
            return round(total_score, 2)
        except Exception as e:
            print(f"Trend score hesaplama hatasi: {e}")
            return 0

@api_view(['GET'])
@permission_classes([AllowAny])
def trending_files(request):
    try:
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        trending_shares = FileShare.objects.filter(
            share_type='public',
            created_at__gte=thirty_days_ago
        ).select_related('file', 'created_by')
        
        shares_with_scores = []
        for share in trending_shares:
            score = TrendingAlgorithm.calculate_trend_score(share)
            shares_with_scores.append((share, score))
        
        shares_with_scores.sort(key=lambda x: x[1], reverse=True)
        sorted_shares = [share for share, score in shares_with_scores[:50]]
        
        serializer = FileShareSerializer(sorted_shares, many=True, context={'request': request})
        return Response(serializer.data)
    except Exception as e:
        print(f"Trending files hatasi: {e}")
        return Response({"error": "Trend verileri yuklenirken hata olustu"}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny]) # Trend listesi herkese açık olabilir
def trending_files_view(request):
    """
    Herkese açık olarak paylaşılan dosyaları bir trend mekanizmasına göre sıralar.
    Trend Puanı = (Görüntüleme Sayısı) + (Zaman Yakınlığı Katsayısı)
    """
    
    # Sadece 'public' (Herkese Açık) paylaşımları seç
    public_shares = FileShare.objects.filter(share_type='public', file__isnull=False)
    
    # 24 saatten eski dosyaların trend puanını düşürmek için katsayı hesapla
    now = timezone.now()
    one_day_ago = now - timedelta(days=1)
    
    # Trend puanı hesaplama mantığı
    # Zaman Yakınlığı Katsayısı: Dosya ne kadar yeniyse o kadar yüksek (Max: 10, Min: 1)
    # Basit bir formül: 
    # Yeni dosyalar için (son 24 saat) -> 10 + view_count
    # Eski dosyalar için (24 saatten sonra her gün için düşüş katsayısı) -> view_count * (1 / (gün_farkı))
    
    # Görüntüleme sayısı büyük bir etken olduğu için basit bir ağırlık kullanalım:
    # Trend Puanı = view_count + (10 / (güncel zaman - created_at_gün_farkı + 1))
    
    # Django ORM'de karmaşık matematiksel hesaplama yapmak yerine,
    # basit bir ağırlıklı sıralama yapalım (önce görüntüleme, sonra tarih) veya
    # QuerySet'i filtreleyip Python'da trend puanını hesaplayalım.
    
    # Python'da trend puanı hesaplama (daha esnek bir trend algoritması için):
    trending_list = []
    
    for share in public_shares:
        time_diff = now - share.created_at
        
        # Zaman ağırlığı: Son 24 saat 100 puan, 2-7 gün 50 puan, sonrası 10 puan
        if time_diff < timedelta(hours=24):
            time_weight = 100
        elif time_diff < timedelta(days=7):
            time_weight = 50
        else:
            time_weight = 10
            
        # Trend Puanı = (Görüntüleme Sayısı * 2) + Zaman Ağırlığı
        trend_score = (share.view_count * 2) + time_weight
        
        share.trend_score = trend_score # Serizlier'ın okuması için objeye ekliyoruz
        trending_list.append(share)
        
    # Trend puanına göre büyükten küçüğe sırala
    trending_list.sort(key=lambda x: x.trend_score, reverse=True)
    
    # İlk 50 trend dosyayı al
    top_trending = trending_list[:50]

    # Serizializer ile veriyi formatla
    serializer = FileShareSerializer(top_trending, many=True, context={'request': request})
    
    return Response(serializer.data)

# Bu görünümü bir `urls.py` dosyasına `/api/trending/` olarak eklemeyi unutmayın.
@api_view(['GET'])
@permission_classes([AllowAny])
def trending_by_category(request, category):
    try:
        file_extensions = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
            'video': ['.mp4', '.avi', '.mov', '.mkv'],
            'document': ['.pdf', '.doc', '.docx', '.txt'],
            'audio': ['.mp3', '.wav', '.ogg']
        }
        
        extensions = file_extensions.get(category, [])
        
        if not extensions:
            return Response({"error": "Gecersiz kategori"}, status=400)
        
        trending_shares = FileShare.objects.filter(
            share_type='public',
            file__file__endswith=tuple(extensions)
        )
        
        shares_with_scores = []
        for share in trending_shares:
            score = TrendingAlgorithm.calculate_trend_score(share)
            shares_with_scores.append((share, score))
        
        shares_with_scores.sort(key=lambda x: x[1], reverse=True)
        sorted_shares = [share for share, score in shares_with_scores[:20]]
        
        serializer = FileShareSerializer(sorted_shares, many=True, context={'request': request})
        return Response(serializer.data)
    except Exception as e:
        print(f"Trending category hatasi: {e}")
        return Response({"error": "Kategori verileri yuklenirken hata olustu"}, status=500)


@api_view(['GET'])
@permission_classes([AllowAny]) # Arama motoru herkese açık olabilir
def search_public_files_view(request):
    """
    Herkese açık olarak paylaşılan dosyaları arama sorgusuna göre filtreler.
    Sadece 'public' (Herkese Açık) paylaşımları döndürür.
    """
    
    # URL'den arama sorgusunu al (?q=anahtar_kelime)
    query = request.query_params.get('q', None)
    
    if not query:
        # Arama sorgusu yoksa boş sonuç döndür
        return Response({
            'fileshares': [], 
            'message': 'Lütfen bir arama kelimesi girin.'
        }, status=200)

    # 1. Sadece 'public' (Herkese Açık) paylaşımları filtrele
    public_shares_queryset = FileShare.objects.filter(share_type='public', file__isnull=False)
    
    # 2. Arama Kriterlerini belirle
    # Arama kriterleri: Dosya adı VEYA paylaşımı oluşturan kullanıcı adı
    search_criteria = Q(file__file__icontains=query) | Q(created_by__username__icontains=query)
    
    # 3. Kriterlere uyan paylaşımları filtrele
    search_results = public_shares_queryset.filter(search_criteria).distinct()
    
    # NOT: Trend API'sinde kullanılan mantıkla uyumlu olması için, 
    # dilerseniz arama sonuçlarını da görüntülenme sayısına göre sıralayabilirsiniz:
    # search_results = search_results.order_by('-view_count') 
    
    # Serizializer'ı kullanarak veriyi formatla
    # Trend puanı ve yüklenme zamanı bilgileri de otomatik olarak hesaplanacaktır.
    from .serializers import FileShareSerializer # Serializer'ı import edin
    
    serializer = FileShareSerializer(
        search_results, 
        many=True, 
        context={'request': request}
    )
    
    return Response({
        'fileshares': serializer.data, # Sonuçları 'fileshares' anahtarıyla döndür
        'message': f"'{query}' için {search_results.count()} sonuç bulundu."
    })


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_device(request):
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
    device_uuid = request.headers.get("X-Device-UUID") or request.query_params.get("device_uuid")
    if not device_uuid:
        return Response({"error": "device_uuid gerekli"}, status=400)

    try:
        device_uuid_obj = uuid.UUID(device_uuid)
    except ValueError:
        return Response({"error": "gecersiz UUID"}, status=400)

    if not Device.objects.filter(user=request.user, device_uuid=device_uuid_obj).exists():
        return Response({"error": "cihaz dogrulamasi basarisiz"}, status=403)

    file_path = os.path.join(settings.MEDIA_ROOT, file_name)
    if not os.path.exists(file_path):
        return HttpResponse("Dosya bulunamadi", status=404)
    
    return FileResponse(open(file_path, "rb"), as_attachment=True)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def intelligent_search(request):
    """Akilli arama API'si"""
    from memory.services.advanced_memory_manager import BasicMemoryManager
    from memory.utils import get_behavioral_suggestions, rank_results_with_context
    
    query = request.data.get('query', '')
    file_type = request.data.get('file_type')
    
    if not query:
        return Response({'error': 'Arama sorgusu gerekli'}, status=400)
    
    try:
        memory_manager = BasicMemoryManager(request.user)
        
        # Basit dosya araması (şimdilik filename-based)
        from .models import File
        file_results = File.objects.filter(
            owner=request.user,
            name__icontains=query
        )[:10]
        
        results = []
        for file in file_results:
            results.append({
                'file_path': file.name,
                'file_type': getattr(file, 'content_type', 'unknown'),
                'similarity_score': 0.8,  # Basit skor
                'last_accessed': file.uploaded_at,
                'access_count': 1
            })
        
        behavioral_suggestions = get_behavioral_suggestions(request.user, query)
        ranked_results = rank_results_with_context(results, behavioral_suggestions, request.user)
        
        return Response({
            'query': query,
            'semantic_results': ranked_results,
            'behavioral_suggestions': behavioral_suggestions
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_contextual_suggestions(request):
    """Context onerileri API'si"""
    from memory.utils import analyze_user_context
    
    try:
        context = analyze_user_context(request.user)
        
        # Basit öneriler
        suggestions = [
            {
                'type': 'recent_activity',
                'content': 'Son yuklediginiz dosyalari goruntuleyin',
                'confidence': 0.7
            }
        ]
        
        return Response({
            'context': context,
            'suggestions': suggestions
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@csrf_exempt
@require_POST
def login_view(request):
    try:
        data = json.loads(request.body)
        return JsonResponse({'user': {'email': data['email']}})
    except Exception as e:
        return JsonResponse({'detail': str(e)}, status=400)

@csrf_exempt
@require_POST
def signup_view(request):
    try:
        data = json.loads(request.body)
        return JsonResponse({'user': {'email': data['email']}})
    except Exception as e:
        return JsonResponse({'detail': str(e)}, status=400)

@api_view(['GET'])
@permission_classes([AllowAny])
def debug_check(request):
    """Temporary debug endpoint to check system status"""
    from django.conf import settings
    from django.db import connection
    import sys
    
    debug_info = {
        'django_version': sys.version,
        'debug_mode': settings.DEBUG,
        'database_connected': connection.is_usable(),
        'installed_apps': [app for app in settings.INSTALLED_APPS if 'memory' in app or 'your_app' in app],
    }
    
    return Response(debug_info)

