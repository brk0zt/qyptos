import threading
from users.security.camera_detector import security_detector
from django.utils.deprecation import MiddlewareMixin
import time

GRACE_PERIOD_SECONDS = 5

class CameraSecurityMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # 1. Kontrol: Sadece tek kullanýmlýk medya görüntüleme endpoint'lerinde çalýþsýn
        is_share_endpoint = any(path in request.path for path in ['/one-time-view/', '/share/'])
        
        # 2. Medya dosyasý API çaðrýlarýný yok say (Örn: /media/uploads/...)
        # Bu, statik dosyalarýn ve direkt API çaðrýlarýnýn kamerayý tetiklemesini engeller.
        if request.path.startswith('/api/') and not request.path.startswith('/api/secure-media/'):
            return None # API çaðrýlarýný atla
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return None # Statik/Medya dosyalarýný atla

        if is_share_endpoint:
            
            # Thread henüz çalýþmýyorsa baþlat
            if not security_detector.is_monitoring:
                # YENÝ EKLENTÝ/DÜZELTME: Ýzlemeye baþlamadan önce *mevcut* ihlal durumunu temizle!
                security_detector.security_breach = False 
                # Sadece bir kere ve ana istekte baþlatýlmasýný saðla
                security_thread = threading.Thread(target=security_detector.start_monitoring)
                security_thread.daemon = True
                security_thread.start()
                

                is_in_grace_period = (
                security_detector.is_monitoring and
                security_detector.start_time != 0 and
                (time.time() - security_detector.start_time) < GRACE_PERIOD_SECONDS
            )
                if security_detector.security_breach and not is_in_grace_period: 
                # Middleware'den direkt yanýt döndürmek, isteðin view'a ulaþmasýný engeller.
                    pass
        return None # Devam et
    
    # process_response kýsmý ayný kalabilir.
    def process_response(self, request, response):
        # Güvenlik ihlali varsa özel header ekle (Frontend bu header'ý okuyacak)
        if security_detector.security_breach:
            response['X-Security-Breach'] = 'CAMERA_DETECTED'
            # Ýhlal sinyali gönderildiði için, bir sonraki isteði temizleyelim.
            # security_detector.security_breach = False # Bu, Frontend tarafýndan yönetilmelidir.
            
        return response
