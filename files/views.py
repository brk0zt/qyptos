# -*- coding: utf-8 -*-
import os
import json
import uuid
import base64
import secrets
import mimetypes
import logging
import time
from datetime import timedelta

import numpy as np
import cv2
from PIL import Image

from django.shortcuts import render, get_object_or_404, redirect
from django.http import (
    HttpResponse, JsonResponse, FileResponse, 
    HttpResponseForbidden, HttpResponseGone
)
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.cache import cache
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_http_methods
from django.db import models
from django.db.models import Count, Q, F, ExpressionWrapper, FloatField
from django.db.models.functions import Coalesce

from rest_framework import (
    status, generics, permissions, viewsets, 
    serializers, mixins
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser

from .models import (
    File, CloudGroup, GroupFile, FileComment, 
    SecureLink, MediaFile, FileShare, GroupInvite, GroupMember
)
from .serializers import (
    FileSerializer, CloudGroupSerializer, GroupFileSerializer,
    FileCommentSerializer, GroupInviteSerializer, FileShareSerializer,
    SecureLinkSerializer, MediaFileSerializer
)
from .utils import add_watermark

from users.models import Device
from users.security.camera_detector import security_detector

from memory.models import MemoryItem, MemoryTier, VideoFrame
from memory.services.ai_services import AIService

logger = logging.getLogger(__name__)

# OpenCV fallback mekanizması
try:
    import cv2
    OPENCV_AVAILABLE = True
    logger.info("OpenCV başarıyla yüklendi")
except ImportError:
    OPENCV_AVAILABLE = False
    logger.warning("OpenCV yüklenemedi, Pillow kullanılacak")


# ==================== YARDIMCI FONKSİYONLAR ====================

def get_client_ip(request):
    """İstemci IP adresini al"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def serve_file_directly(file_obj):
    """Ortak dosya sunma fonksiyonu"""
    try:
        if not file_obj or not file_obj.file:
            print("❌ File object or file field is missing")
            return Response(
                {"error": "Dosya objesi bulunamadı"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        file_path = file_obj.file.path
        print(f"✅ Serving file: {file_path}")
        
        if not os.path.exists(file_path):
            print(f"❌ File not found on disk: {file_path}")
            return Response(
                {"error": "Dosya diskte bulunamadı"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        content_type, encoding = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'
        
        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type,
            as_attachment=False
        )
        
        filename = os.path.basename(file_path)
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        print(f"✅ File served successfully: {filename}")
        return response
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        return Response(
            {"error": "Dosya diskte bulunamadı"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return Response(
            {"error": f"Dosya sunulurken hata oluştu: {str(e)}"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def render_secure_html_page(request, file_obj):
    """Güvenli HTML sayfası oluştur"""
    file_url = request.build_absolute_uri(file_obj.file.url)
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
                margin: 0; padding: 0; background: #0a0a0a; color: white;
                font-family: Arial, sans-serif; overflow: hidden;
                user-select: none; -webkit-user-select: none;
            }}
            .secure-container {{
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                display: flex; flex-direction: column; align-items: center;
                justify-content: center; background: #000;
            }}
            .media-container {{
                max-width: 95%; max-height: 80vh; position: relative;
                border: 3px solid #ff4444; border-radius: 8px;
                overflow: hidden; background: #000;
            }}
            .media-container img, .media-container video {{
                max-width: 100%; max-height: 80vh; display: block;
            }}
            .protection-overlay {{
                position: absolute; top: 0; left: 0; width: 100%; height: 100%;
                pointer-events: none; z-index: 9998;
            }}
            .watermark {{
                position: absolute; bottom: 10px; right: 10px;
                color: rgba(255, 255, 255, 0.3); font-size: 12px;
                background: rgba(0, 0, 0, 0.5); padding: 5px 10px;
                border-radius: 3px; pointer-events: none; z-index: 9999;
            }}
            .header {{
                position: absolute; top: 20px; left: 0; width: 100%;
                text-align: center; color: #ff4444; font-weight: bold; z-index: 10000;
            }}
        </style>
    </head>
    <body>
        <div class="secure-container">
            <div class="header">🔒 GÜVENLİ GÖRÜNTÜLEYİCİ</div>
            <div class="media-container" id="mediaContainer">
                {"<video controls src='" + file_url + "'></video>" if is_video else "<img src='" + file_url + "'>"}
                <div class="protection-overlay"></div>
                <div class="watermark">
                    {file_obj.owner.username if file_obj.owner else 'Kullanıcı'} | {timezone.now().strftime('%d.%m.%Y %H:%M')}
                </div>
            </div>
        </div>
        <script>
            let violationCount = 0;
            const maxViolations = 2;
            
            document.addEventListener('keydown', function(e) {{
                const screenshotKeys = ['PrintScreen', 'Snapshot', 'F13', 'F14', 'F15'];
                if (screenshotKeys.includes(e.key)) {{
                    e.preventDefault();
                    violationCount++;
                    alert('🚫 EKRAN GÖRÜNTÜSÜ ALINAMAZ!');
                    if (violationCount >= maxViolations) {{
                        document.body.innerHTML = '<div style="width:100vw;height:100vh;background:black;color:red;display:flex;align-items:center;justify-content:center;flex-direction:column;"><h1>GÜVENLİK İHLALİ</h1></div>';
                    }}
                }}
            }}, true);
            
            document.addEventListener('contextmenu', function(e) {{
                e.preventDefault();
                return false;
            }}, true);
        </script>
    </body>
    </html>
    """
    return HttpResponse(html_content)


# ==================== TREND ALGORİTMASI ====================

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
            print(f"Trend score hesaplama hatası: {e}")
            return 0


# ==================== GÜVENLİK MİDDLEWARE ====================

class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if '/share/' in request.path:
            user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
            suspicious_agents = ['bot', 'crawler', 'scraper', 'screenshot']
            if any(agent in user_agent for agent in suspicious_agents):
                return JsonResponse({'error': 'Güvenlik ihlali tespit edildi'}, status=403)
        response = self.get_response(request)
        return response


# ==================== DOSYA YÖNETİMİ ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_file(request):
    """Dosya yükleme endpoint'i - OpenCV/Pillow uyumlu"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'Dosya bulunamadı'}, status=400)
        
        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name
        file_size = uploaded_file.size
        
        width, height = None, None
        file_type = uploaded_file.content_type or 'unknown'
        
        if file_type.startswith('image/'):
            try:
                if OPENCV_AVAILABLE:
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
                    image = Image.open(uploaded_file)
                    width, height = image.size
            except Exception as e:
                logger.warning(f"Görsel boyutu alınamadı: {e}")
        
        uploaded_file.seek(0)
        file_path = default_storage.save(file_name, ContentFile(uploaded_file.read()))
        
        try:
            from memory.services.advanced_memory_manager import AdvancedMemoryManager
            memory_manager = AdvancedMemoryManager(request.user)
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
@permission_classes([IsAuthenticated])
def list_files(request):
    """Kullanıcının dosyalarını listele"""
    try:
        files = []
        return JsonResponse({'files': files})
    except Exception as e:
        logger.error(f"Dosya listeleme hatası: {e}")
        return JsonResponse({'error': str(e)}, status=500)


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


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def download_file(request, file_id):
    """Dosya indirme - Range desteği ile"""
    file_obj = get_object_or_404(File, id=file_id)

    if file_obj.one_time_view and file_obj.is_consumed:
        return HttpResponseGone(
            '{"detail": "Bu dosya zaten görüntülendi ve artık kullanılamaz."}', 
            content_type='application/json'
        )

    file_path = file_obj.file.path
    if not os.path.exists(file_path):
        return HttpResponse("Dosya bulunamadı", status=404)
    
    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("Range", "").strip()

    if range_header:
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
        return response
    else:
        response = FileResponse(
            open(file_path, "rb"), 
            as_attachment=True, 
            filename=os.path.basename(file_path)
        )
        response["Accept-Ranges"] = "bytes"
        return response


def consume_file(request, file_id):
    """Dosya tüketme endpoint'i"""
    if request.method == 'POST':
        file_obj = get_object_or_404(File, id=file_id)
    
        if not file_obj.one_time_view:
            return JsonResponse({'detail': 'Bu dosya tek gösterimlik değil.'}, status=400)
        
        if file_obj.is_consumed:
            return JsonResponse({'detail': 'Bu dosya zaten tüketildi.'}, status=410)
        
        file_obj.is_consumed = True
        file_obj.save()
        file_obj.file.delete()
        
        return JsonResponse({'detail': 'Dosya başarıyla tüketildi.'}, status=200)
    
    return JsonResponse({'detail': 'Sadece POST metoduna izin verilir.'}, status=405)


# ==================== GÜVENLİ MEDYA PAYLAŞIMI ====================

def share_file_view(request, token):
    """Güvenli paylaşım sayfası"""
    try:
        share = FileShare.objects.get(token=token)
    except FileShare.DoesNotExist:
        return render(request, 'index.html', {'error': 'Paylaşım bulunamadı.'})

    is_consumed_by_backend = not share.is_valid()
    
    if not share.is_valid():
        print("------------------------------------------")
        print("HATA AYIKLAMA: DOSYA GEÇERSİZ SAYILIYOR")
        print(f"Token: {token}")
        print(f"is_expired: {share.is_expired()}")
        print(f"is_revoked: {share.is_revoked}")
        print(f"view_count: {share.view_count}, max_views: {share.max_views}")
        print("------------------------------------------")
    
    context = {
        'is_consumed_by_backend': is_consumed_by_backend,
    }
    return render(request, 'frontend/build/index.html', context)


@api_view(['GET'])
@permission_classes([AllowAny])
def secure_file_view(request, token):
    """Token tabanlı güvenli dosya görüntüleme"""
    try:
        share = FileShare.objects.get(token=token, is_revoked=False)
    except FileShare.DoesNotExist:
        return HttpResponseForbidden("Erişim reddedildi.")

    if share.is_expired():
        return HttpResponseGone("Bu paylaşım süresi doldu.")
    
    if share.view_count >= share.max_views:
        return HttpResponseGone("Maksimum görüntüleme sayısına ulaşıldı.")

    try:
        share.view_count += 1
        share.save()
        
        file_object = share.file.file
        file_path = file_object.path
    except Exception:
        return HttpResponseGone("Dosya içeriği bulunamadı.")
    
    content_type = file_object.file.content_type if hasattr(
        file_object.file, 'content_type'
    ) else 'application/octet-stream'

    response = FileResponse(open(file_path, 'rb'), content_type=content_type)
    response['Content-Disposition'] = f'inline; filename="{file_object.name}"'
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['X-Content-Type-Options'] = 'nosniff'

    return response


@api_view(['GET'])
@permission_classes([AllowAny])
def secure_media_view(request, token):
    """Güvenli medya dosyasını sunar"""
    file_obj = None
    file_share = None

    try:
        try:
            file_share = FileShare.objects.select_related('file').get(
                token=token, is_revoked=False
            )
            file_obj = file_share.file
        except FileShare.DoesNotExist:
            try:
                file_obj = File.objects.get(view_token=token)
            except File.DoesNotExist:
                return Response({"error": "Geçersiz token"}, status=404)

        is_already_consumed = False
        if file_share:
            if file_share.view_count >= file_share.max_views:
                is_already_consumed = True
        elif file_obj and file_obj.one_time_view and file_obj.has_been_viewed:
            is_already_consumed = True

        if is_already_consumed:
            return Response({"error": "Bu medya zaten tüketildi."}, status=410)

        if not file_obj or not file_obj.file:
            return Response({"error": "Dosya bulunamadı"}, status=404)

        file_path = file_obj.file.path
        if not os.path.exists(file_path):
            return Response({"error": "Dosya diskte bulunamadı"}, status=404)

        content_type, encoding = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'

        if file_share:
            file_share.view_count += 1
            file_share.save()
        elif file_obj and file_obj.one_time_view and not file_obj.has_been_viewed:
            file_obj.has_been_viewed = True
            file_obj.save()

        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        filename = os.path.basename(file_path)
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        response['X-Content-Type-Options'] = 'nosniff'

        return response

    except Exception as e:
        print(f"Secure media error: {str(e)}")
        return Response({"error": "Dosya sunulurken hata oluştu"}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def revoke_share(request, share_id):
    """Paylaşımı iptal et"""
    share = get_object_or_404(FileShare, id=share_id, created_by=request.user)
    share.is_revoked = True
    share.save()
    return Response({"message": "Paylaşım iptal edildi ve pasif hale getirildi."})


# ==================== GÜVENLİK KAMERA ====================

@require_POST
def stop_camera_monitoring(request):
    """Kamera izlemeyi durdur"""
    security_detector.stop_monitoring()
    return JsonResponse(
        {"status": "ok", "message": "Camera monitoring stopped."}, 
        status=200
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def analyze_camera_frame(request):
    """Frontend'den gelen frame'i analiz eder"""
    try:
        frame_file = request.FILES.get('frame')
        if not frame_file:
            return Response({'error': 'Frame bulunamadı'}, status=400)
        
        file_bytes = np.frombuffer(frame_file.read(), np.uint8)
        frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        if frame is None:
            return Response({'error': 'Frame decode edilemedi'}, status=400)
        
        security_status = security_detector.monitor_security(frame)
        
        if security_status == "BLOCK_SCREEN":
            request.session['security_breach'] = True
            request.session.modified = True
            print(f"🚨 Session {request.session.session_key} için ihlal işaretlendi.")
        
        is_breached = request.session.get('security_breach', False)
        
        return Response({
            'security_breach': is_breached,
            'reason': 'CAMERA_DETECTED' if is_breached else 'CLEAR',
            'face_detected': security_detector.detect_faces(frame),
            'lens_detected': security_detector.multi_method_lens_detection(frame)
        })
        
    except Exception as e:
        print(f"Frame analiz hatası: {str(e)}")
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def report_security_breach(request):
    """Manuel güvenlik ihlali bildirimi"""
    try:
        data = request.data
        reason = data.get('reason', 'UNKNOWN')
        
        request.session['security_breach'] = True
        request.session.modified = True
        
        print(f"🚨 GÜVENLİK İHLALİ RAPORLANDI (Session): {reason}")
        
        return Response({'status': 'reported', 'action': 'BLOCK_SESSION'})
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def clear_security_breach(request):
    """DEBUG: Güvenlik ihlalini temizle"""
    request.session['security_breach'] = False
    return Response({'status': 'cleared'})


class SecureMediaView(APIView):
    """Güvenli medya görüntüleme - Session tabanlı"""
    permission_classes = [AllowAny]
    
    def get(self, request, token):
        try:
            security_check = self.check_security(request)
            if not security_check['allowed']:
                return self.render_security_block(security_check['reason'])
            
            share = get_object_or_404(FileShare, token=token, is_revoked=False)
            
            if share.is_expired() or share.view_count >= share.max_views:
                return self.render_security_block("Link süresi doldu veya limit aşıldı.")

            share.view_count += 1
            share.save()
            
            return FileResponse(share.file.file.open('rb'))
            
        except Exception as e:
            return Response({'error': str(e)}, status=500)
    
    def check_security(self, request):
        """Session kontrolü"""
        backend_breach = request.session.get('security_breach', False)
        return {
            'allowed': not backend_breach,
            'reason': 'CAMERA_DETECTED_SESSION' if backend_breach else 'CLEAR'
        }
    
    def render_security_block(self, reason):
        """Güvenlik engelleme sayfası"""
        html_content = f"""
        <html>
        <body style="background:black; color:red; text-align:center; padding:50px;">
            <div style="font-size:50px;">🚫</div>
            <h1>Erişim Engellendi</h1>
            <p>Güvenlik sistemi bir ihlal tespit etti.</p>
            <p>Kod: {reason}</p>
        </body>
        </html>
        """
        return HttpResponse(html_content, status=403)


# ==================== TREND VE ARAMA ====================

@api_view(['GET'])
@permission_classes([AllowAny])
def trending_files(request):
    """Trend dosyaları listele"""
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
        
        serializer = FileShareSerializer(
            sorted_shares, many=True, context={'request': request}
        )
        return Response(serializer.data)
    except Exception as e:
        print(f"Trending files hatası: {e}")
        return Response(
            {"error": "Trend verileri yüklenirken hata oluştu"}, 
            status=500
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def trending_by_category(request, category):
    """Kategoriye göre trend dosyalar"""
    try:
        file_extensions = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
            'video': ['.mp4', '.avi', '.mov', '.mkv'],
            'document': ['.pdf', '.doc', '.docx', '.txt'],
            'audio': ['.mp3', '.wav', '.ogg']
        }
        
        extensions = file_extensions.get(category, [])
        if not extensions:
            return Response({"error": "Geçersiz kategori"}, status=400)
        
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
        
        serializer = FileShareSerializer(
            sorted_shares, many=True, context={'request': request}
        )
        return Response(serializer.data)
    except Exception as e:
        print(f"Trending category hatası: {e}")
        return Response(
            {"error": "Kategori verileri yüklenirken hata oluştu"}, 
            status=500
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def search_public_files_view(request):
    """Herkese açık dosyalarda arama"""
    query = request.query_params.get('q', None)
    
    if not query:
        return Response({
            'fileshares': [], 
            'message': 'Lütfen bir arama kelimesi girin.'
        }, status=200)

    public_shares_queryset = FileShare.objects.filter(
        share_type='public', file__isnull=False
    )
    
    search_criteria = Q(file__file__icontains=query) | Q(
        created_by__username__icontains=query
    )
    search_results = public_shares_queryset.filter(search_criteria).distinct()
    
    serializer = FileShareSerializer(
        search_results, many=True, context={'request': request}
    )
    
    return Response({
        'fileshares': serializer.data,
        'message': f"'{query}' için {search_results.count()} sonuç bulundu."
    })


# ==================== SECURE LINK ====================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_secure_link(request, file_id):
    """Güvenli link oluştur"""
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
    """Token ile dosya indir"""
    link = get_object_or_404(SecureLink, token=token)
    if not link.is_valid():
        return HttpResponseForbidden("Link expired or max uses reached")
    link.used_count += 1
    link.save()
    return FileResponse(link.file.file.open("rb"), as_attachment=True)


# ==================== GRUP YÖNETİMİ ====================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_invite(request):
    """Gruba davet gönder"""
    group_id = request.data.get("group_id")
    email = request.data.get("email")

    try:
        group = CloudGroup.objects.get(id=group_id, owner=request.user)
    except CloudGroup.DoesNotExist:
        return Response(
            {"error": "Group not found or you are not the owner"}, 
            status=403
        )

    invite = GroupInvite.objects.create(
        group=group, email=email, invited_by=request.user
    )
    serializer = GroupInviteSerializer(invite)
    return Response(serializer.data, status=201)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def accept_invite(request):
    """Grup davetini kabul et"""
    invite_id = request.data.get("invite_id")

    try:
        invite = GroupInvite.objects.get(
            id=invite_id, email=request.user.email, accepted=False
        )
    except GroupInvite.DoesNotExist:
        return Response({"error": "No pending invite found"}, status=404)

    GroupMember.objects.create(group=invite.group, user=request.user, role="member")
    invite.accepted = True
    invite.save()

    return Response({"message": f"Joined group {invite.group.name}"}, status=200)


# ==================== CİHAZ KAYDI ====================

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_device(request):
    """Cihaz kaydı"""
    device_uuid = request.data.get("device_uuid")
    device_name = request.data.get("device_name", "")
    
    if not device_uuid:
        return Response({"error": "device_uuid gerekli"}, status=400)

    try:
        device_uuid_obj = uuid.UUID(device_uuid)
    except ValueError:
        return Response({"error": "geçersiz UUID"}, status=400)

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
    """Cihaz doğrulama ile dosya erişimi"""
    device_uuid = request.headers.get("X-Device-UUID") or request.query_params.get(
        "device_uuid"
    )
    
    if not device_uuid:
        return Response({"error": "device_uuid gerekli"}, status=400)

    try:
        device_uuid_obj = uuid.UUID(device_uuid)
    except ValueError:
        return Response({"error": "geçersiz UUID"}, status=400)

    if not Device.objects.filter(
        user=request.user, device_uuid=device_uuid_obj
    ).exists():
        return Response({"error": "cihaz doğrulaması başarısız"}, status=403)

    file_path = os.path.join(settings.MEDIA_ROOT, file_name)
    if not os.path.exists(file_path):
        return HttpResponse("Dosya bulunamadı", status=404)
    
    return FileResponse(open(file_path, "rb"), as_attachment=True)


# ==================== AKILLI ARAMA ====================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def intelligent_search(request):
    """Akıllı arama API'si"""
    from memory.services.advanced_memory_manager import AdvancedMemoryManager
    from memory.utils import get_behavioral_suggestions, rank_results_with_context
    
    query = request.data.get('query', '')
    file_type = request.data.get('file_type')
    
    if not query:
        return Response({'error': 'Arama sorgusu gerekli'}, status=400)
    
    try:
        memory_manager = AdvancedMemoryManager(request.user)
        
        from .models import File
        file_results = File.objects.filter(
            owner=request.user, name__icontains=query
        )[:10]
        
        results = []
        for file in file_results:
            results.append({
                'file_path': file.name,
                'file_type': getattr(file, 'content_type', 'unknown'),
                'similarity_score': 0.8,
                'last_accessed': file.uploaded_at,
                'access_count': 1
            })
        
        behavioral_suggestions = get_behavioral_suggestions(request.user, query)
        ranked_results = rank_results_with_context(
            results, behavioral_suggestions, request.user
        )
        
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
    """Context önerileri API'si"""
    from memory.utils import analyze_user_context
    
    try:
        context = analyze_user_context(request.user)
        
        suggestions = [
            {
                'type': 'recent_activity',
                'content': 'Son yüklediğiniz dosyaları görüntüleyin',
                'confidence': 0.7
            }
        ]
        
        return Response({'context': context, 'suggestions': suggestions})
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)


# ==================== AUTH ====================

@csrf_exempt
@require_http_methods(["POST"])
def kayit_api(request):
    """Kullanıcı kaydı"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            
            user = User.objects.create_user(
                username=username, email=email, password=password
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Kullanıcı başarıyla kaydedildi',
                'user_id': user.id
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Hata: {str(e)}'})


@csrf_exempt
@require_POST
def login_view(request):
    """Login"""
    try:
        data = json.loads(request.body)
        return JsonResponse({'user': {'email': data['email']}})
    except Exception as e:
        return JsonResponse({'detail': str(e)}, status=400)


@csrf_exempt
@require_POST
def signup_view(request):
    """Signup"""
    try:
        data = json.loads(request.body)
        return JsonResponse({'user': {'email': data['email']}})
    except Exception as e:
        return JsonResponse({'detail': str(e)}, status=400)


@api_view(['GET'])
@permission_classes([AllowAny])
def debug_check(request):
    """Debug endpoint"""
    from django.conf import settings
    from django.db import connection
    import sys
    
    debug_info = {
        'django_version': sys.version,
        'debug_mode': settings.DEBUG,
        'database_connected': connection.is_usable(),
        'installed_apps': [
            app for app in settings.INSTALLED_APPS 
            if 'memory' in app or 'your_app' in app
        ],
    }
    
    return Response(debug_info)


# ==================== VIEWSETS ====================

class MediaFileViewSet(viewsets.ModelViewSet):
    """Media dosya yönetimi"""
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

                add_watermark(
                    original_path, watermarked_path, 
                    username=self.request.user.username
                )

                with open(watermarked_path, "rb") as f:
                    instance.file.save(
                        os.path.basename(watermarked_path), 
                        ContentFile(f.read()), 
                        save=True
                    )

                if os.path.exists(original_path):
                    os.remove(original_path)
                if os.path.exists(watermarked_path):
                    os.remove(watermarked_path)
                    
            except Exception as e:
                print(f"Watermark hatası: {str(e)}")


class FileUploadListView(
    mixins.ListModelMixin, mixins.CreateModelMixin, generics.GenericAPIView
):
    """Dosya yükleme ve listeleme"""
    serializer_class = FileSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        try:
            qs = File.objects.filter(owner=self.request.user).order_by('-uploaded_at')
            print(f"📁 File count: {qs.count()}")
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
            print("File upload başlıyor...")
            return super().create(request, *args, **kwargs)
        except Exception as e:
            print(f"File upload error: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response(
                {"error": f"Dosya yüklenirken hata oluştu: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def perform_create(self, serializer):
        try:
            file_obj = self.request.data.get("file")
            if not file_obj:
                raise serializers.ValidationError("Dosya seçilmedi")
            
            view_duration = self.request.data.get("view_duration", "unlimited")
            one_time_view = str(self.request.data.get("one_time_view", "False")).lower() in (
                'true', 't', '1', 'on'
            )
            is_public = str(self.request.data.get("is_public", "False")).lower() in (
                'true', 't', '1', 'on'
            )
            
            instance = serializer.save(
                owner=self.request.user, 
                file_size=file_obj.size,
                view_duration=view_duration,
                one_time_view=one_time_view,
                is_public=is_public
            )

            mime_type, _ = mimetypes.guess_type(file_obj.name)
            
            if mime_type and mime_type.startswith("image"):
                try:
                    original_path = instance.file.path
                    if os.path.exists(original_path):
                        base_path = os.path.splitext(original_path)[0]
                        watermarked_path = base_path + "_wm.jpg"
                        
                        add_watermark(
                            original_path, watermarked_path, 
                            username=self.request.user.username
                        )

                        with open(watermarked_path, "rb") as f:
                            instance.file.save(
                                os.path.basename(watermarked_path), 
                                ContentFile(f.read()), 
                                save=True
                            )
                        
                        if os.path.exists(original_path):
                            os.remove(original_path)
                        if os.path.exists(watermarked_path):
                            os.remove(watermarked_path)
                except Exception as e:
                    print(f"Watermark hatası: {e}")

            if instance.one_time_view:
                instance.view_token = str(uuid.uuid4())
                instance.has_been_viewed = False
                instance.save()

            print(f"✅ Dosya yüklendi: {instance.file.name}")

            # AI/Memory İşleme
            try:
                print("🧠 Yapay Hafıza işleniyor...")
                ai_service = AIService()
                default_tier, _ = MemoryTier.objects.get_or_create(name="short_term")
                
                ftype = 'unknown'
                embedding = None
                video_frames_data = []

                if mime_type:
                    if mime_type.startswith('image'): 
                        ftype = 'image'
                        embedding = ai_service.get_image_embedding(instance.file.path)
                    
                    elif mime_type.startswith('text') or mime_type == 'application/pdf' or \
                         instance.file.name.lower().endswith(('.docx', '.py', '.js', '.md')):
                        
                        ftype = 'text'
                        print(f"📄 Metin analizi başlatılıyor: {instance.file.name}")
                        content = ai_service.extract_text_from_file(instance.file.path)
                        
                        if content:
                            combined_text = f"{instance.file.name} : {content[:1000]}"
                            embedding = ai_service.get_text_embedding(combined_text)
                        else:
                            embedding = ai_service.get_text_embedding(instance.file.name)
                    
                    elif mime_type.startswith('video'):
                        ftype = 'video'
                        print(f"🎥 Video analizi: {instance.file.name}")
                        
                        # 1. Kareleri Al
                        video_frames = ai_service.analyze_video_content(instance.file.path, interval_seconds=5)
                        if video_frames: embedding = video_frames[0]['embedding']
                        
                        # 2. Sesi Dinle (YENİ)
                        transcript = ai_service.transcribe_audio(instance.file.path)
                        if transcript:
                            content = f"[TRANSCRIPT]: {transcript}" # content değişkenine ata

                    elif mime_type.startswith('audio'):
                        ftype = 'audio'
                        print(f"🎤 Ses analizi: {instance.file.name}")
                        content = ai_service.transcribe_audio(instance.file.path)
                        if content:
                            embedding = ai_service.get_text_embedding(f"{instance.file.name} : {content[:500]}")
                        else:
                            embedding = ai_service.get_text_embedding(instance.file.name)

                if embedding is not None:
                    emb_bytes = embedding.tobytes() if hasattr(
                        embedding, 'tobytes'
                    ) else embedding

                    memory_item = MemoryItem.objects.create(
                        user=self.request.user,
                        file_name=os.path.basename(instance.file.name),
                        file_path=instance.file.path,
                        file_type=ftype,
                        original_size=instance.file_size,
                        vector_embedding=emb_bytes,
                        memory_tier=default_tier,
                        content_summary=content[:500] if 'content' in locals() and content else None
                    )
                    print(f"🧠 Ana hafıza kaydı oluşturuldu. (ID: {memory_item.id})")

                    if ftype == 'video' and video_frames_data:
                        for frame in video_frames_data:
                            VideoFrame.objects.create(
                                memory_item=memory_item,
                                timestamp=frame['timestamp'],
                                vector_embedding=frame['embedding'].tobytes()
                            )
                        print(f"   ↳ {len(video_frames_data)} adet video karesi işlendi.")

                else:
                    print("⚠️ Vektör oluşturulamadı.")

            except Exception as e:
                print(f"❌ Hafıza oluşturma hatası: {e}")
                import traceback
                traceback.print_exc()

        except Exception as e:
            print(f"Dosya yükleme hatası: {e}")
            raise


class FileShareViewSet(viewsets.ModelViewSet):
    """Dosya paylaşım yönetimi"""
    serializer_class = FileShareSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return FileShare.objects.filter(created_by=self.request.user)
    
    def perform_create(self, serializer):
        file_id = self.request.data.get('file')
        file = get_object_or_404(File, id=file_id, owner=self.request.user)
        share = serializer.save(created_by=self.request.user, file=file)


class FileDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Dosya detay görünümü"""
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
    """Tek seferlik dosya görüntüleme"""
    permission_classes = [permissions.AllowAny]
    serializer_class = FileSerializer
    
    @method_decorator(never_cache)
    def get(self, request, token):
        try:
            file_obj = File.objects.get(view_token=token)
            print(f"✅ Dosya bulundu, Token: {token}")
        except File.DoesNotExist:
            print(f"❌ Token ile dosya bulunamadı: {token}")
            return Response(
                {'detail': 'Geçersiz veya Süresi Dolan Dosya'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if file_obj.one_time_view and file_obj.has_been_viewed:
            return Response(
                {'detail': 'Bu dosya zaten görüntülendi ve artık kullanılamaz.'},
                status=status.HTTP_410_GONE
            )

        file_path = file_obj.file.path
        
        try:
            response = FileResponse(open(file_path, 'rb'))
            content_type, encoding = mimetypes.guess_type(file_path)
            response['Content-Type'] = content_type or 'application/octet-stream'
            response['Content-Disposition'] = f'inline; filename="{file_obj.file.name.split("/")[-1]}"'
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
            return response
        
        except FileNotFoundError:
            print(f"❌ Dosya diskte bulunamadı: {file_path}")
            return Response(
                {'detail': 'Dosya diskte bulunamadı.'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"❌ Dosya sunumu hatası: {e}")
            return Response(
                {'detail': 'Beklenmeyen bir hata oluştu.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class FilePreviewView(generics.RetrieveAPIView):
    """Dosya önizleme"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        try:
            file_id = kwargs.get('pk')
            file_obj = get_object_or_404(File, id=file_id, owner=request.user)
            
            if not file_obj.file:
                return Response({"error": "Dosya bulunamadı"}, status=404)
            
            file_name = file_obj.file.name.lower()
            if not any(file_name.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
                return Response(
                    {"error": "Preview sadece görseller için kullanılabilir"}, 
                    status=400
                )
            
            response = FileResponse(
                file_obj.file.open('rb'), content_type='image/jpeg'
            )
            response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_obj.file.name)}"'
            return response
        except Exception as e:
            print(f"Preview error: {str(e)}")
            return Response(
                {"error": f"Dosya açılamadı: {str(e)}"}, 
                status=500
            )


# ==================== GRUP YÖNETİMİ VIEWS ====================

class CloudGroupCreateView(generics.CreateAPIView):
    """Grup oluşturma"""
    serializer_class = CloudGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        group = serializer.save(owner=self.request.user)
        group.members.add(self.request.user)


class CloudGroupJoinView(generics.GenericAPIView):
    """Gruba katılma"""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.data.get('token')
        if not token:
            return Response(
                {'detail':'token required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            group = CloudGroup.objects.get(invite_token=token)
        except CloudGroup.DoesNotExist:
            return Response(
                {'detail':'invalid token'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        group.members.add(request.user)
        return Response({'detail':'joined'})


class CloudGroupListView(generics.ListAPIView):
    """Grup listesi"""
    serializer_class = CloudGroupSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CloudGroup.objects.filter(members=self.request.user)


class CloudGroupDetailView(generics.RetrieveAPIView):
    """Grup detayı"""
    serializer_class = CloudGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = CloudGroup.objects.all()
    
    def get_object(self):
        group = super().get_object()
        if self.request.user not in group.members.all():
            raise PermissionDenied('Bu gruba erişim izniniz yok')
        return group


class GroupFileUploadView(generics.ListCreateAPIView):
    """Grup dosya yükleme"""
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
            watermarked_path = original_path.replace(
                os.path.splitext(original_path)[1], "_wm.jpg"
            )
            add_watermark(
                original_path, watermarked_path, 
                username=self.request.user.username
            )
            with open(watermarked_path, "rb") as f:
                instance.file.save(
                    os.path.basename(watermarked_path), 
                    ContentFile(f.read()), 
                    save=True
                )
            try:
                os.remove(original_path)
                os.remove(watermarked_path)
            except:
                pass
        if instance.one_time_view:
            instance.view_token = uuid.uuid4()
            instance.save()


class GroupFileCommentCreateView(generics.CreateAPIView):
    """Grup dosyasına yorum ekleme"""
    serializer_class = FileCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        file_id = self.kwargs.get('file_id')
        gf = get_object_or_404(GroupFile, pk=file_id)
        group = gf.group
        if self.request.user not in group.members.all():
            raise PermissionDenied('not a member')
        serializer.save(author=self.request.user, file=gf)


# ==================== DİĞER ====================

def range_download_view(request, file_name):
    """Range destekli indirme"""
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)

    if not os.path.exists(file_path):
        return HttpResponse("Dosya bulunamadı", status=404)

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

        response = HttpResponse(
            data, status=206, content_type="application/octet-stream"
        )
        response['Content-Range'] = f"bytes {start}-{end}/{file_size}"
        response['Accept-Ranges'] = "bytes"
        response['Content-Length'] = str(length)
        return response

    return FileResponse(open(file_path, 'rb'), as_attachment=True)