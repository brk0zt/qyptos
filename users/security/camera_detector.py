"""
Kamera ve Yuz Tespit Modulu - Optimize Edilmis Versiyon
False positive'leri minimize etmek icin ayarlanmis
"""

import cv2
import numpy as np
import threading
import time

class SecurityDetector:
    def __init__(self):
        # GÜVENLÝK AYARLARI - False Positive'leri Azaltmak Ýçin
        self.security_breach = False
        self.monitoring_active = False
        self.monitor_thread = None
        
        # THRESHOLD AYARLARI (YÜKSEK = AZ FALSE POSITIVE)
        self.lens_threshold = 0.85  # 0.85'e yükseltildi (önceden 0.5)
        self.face_threshold = 0.7   # Yüz tespiti için eþik
        self.min_detections = 3     # Minimum art arda tespit sayýsý
        self.detection_counter = 0  # Tespit sayacý
        
        # OpenCV Cascade Classifiers
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            self.eye_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_eye.xml'
            )
            print("? OpenCV cascade classifiers yuklendi")
        except Exception as e:
            print(f"?? Cascade classifier yuklenemedi: {e}")
            self.face_cascade = None
            self.eye_cascade = None
    
    def detect_faces(self, frame):
        """Yuz tespiti yap"""
        if frame is None or self.face_cascade is None:
            return False
        
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(60, 60)  # Minimum yüz boyutu
            )
            
            # En az 1 yüz tespit edilirse True
            detected = len(faces) > 0
            
            if detected:
                print(f"?? {len(faces)} yuz tespit edildi")
            
            return detected
            
        except Exception as e:
            print(f"? Yuz tespiti hatasi: {e}")
            return False
    
    def multi_method_lens_detection(self, frame):
        """
        Coklu metod ile lens tespiti
        False positive'leri azaltmak icin kati esik degerleri kullanir
        """
        if frame is None:
            return False
        
        try:
            # Metodlar
            methods = [
                self._detect_circular_lens,
                self._detect_bright_spots,
                self._detect_reflections
            ]
            
            detection_count = 0
            
            for method in methods:
                if method(frame):
                    detection_count += 1
            
            # EN AZ 2 METOD UYUM GÖSTERMELÝ (Katý Kural)
            lens_detected = detection_count >= 2
            
            if lens_detected:
                print(f"?? Lens tespit edildi ({detection_count}/3 metod)")
            
            return lens_detected
            
        except Exception as e:
            print(f"? Lens tespiti hatasi: {e}")
            return False
    
    def _detect_circular_lens(self, frame):
        """Dairesel lens tespiti - YUKSEK THRESHOLD"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (9, 9), 2)
            
            circles = cv2.HoughCircles(
                blurred,
                cv2.HOUGH_GRADIENT,
                dp=1.2,
                minDist=100,
                param1=100,
                param2=50,  # YÜKSEK THRESHOLD (önceden 30)
                minRadius=20,
                maxRadius=150
            )
            
            return circles is not None and len(circles[0]) > 0
            
        except Exception:
            return False
    
    def _detect_bright_spots(self, frame):
        """Parlak nokta tespiti - YUKSEK THRESHOLD"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # ÇOK PARLAK NOKTALAR (250+ yerine 240+)
            _, bright_mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
            
            # Minimum parlak piksel sayýsý
            bright_pixels = np.sum(bright_mask > 0)
            
            # YÜKSEK EÞÝK: Frame'in %0.5'inden fazla parlak piksel olmalý
            threshold = frame.shape[0] * frame.shape[1] * 0.005
            
            return bright_pixels > threshold
            
        except Exception:
            return False
    
    def _detect_reflections(self, frame):
        """Yansima tespiti - YUKSEK THRESHOLD"""
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Çok yüksek parlaklýk ve düþük doygunluk (lens yansýmasý)
            lower = np.array([0, 0, 230])  # V: 230+ (önceden 200)
            upper = np.array([180, 50, 255])  # S: 50'den az
            
            mask = cv2.inRange(hsv, lower, upper)
            reflection_area = np.sum(mask > 0)
            
            # Frame'in %0.3'ünden fazla yansýma olmalý
            threshold = frame.shape[0] * frame.shape[1] * 0.003
            
            return reflection_area > threshold
            
        except Exception:
            return False
    
    def monitor_security(self, frame):
        """
        Ana guvenlik kontrol fonksiyonu
        ART ARDA min_detections KERE TESPIT EDILMELI
        """
        if frame is None:
            return "CLEAR"
        
        try:
            # Yüz ve lens tespiti yap
            face_detected = self.detect_faces(frame)
            lens_detected = self.multi_method_lens_detection(frame)
            
            # HER ÝKÝSÝ DE TESPÝT EDÝLMELÝ
            if face_detected and lens_detected:
                self.detection_counter += 1
                print(f"?? Tespit {self.detection_counter}/{self.min_detections}")
            else:
                # Tespit yoksa sayacý sýfýrla
                self.detection_counter = max(0, self.detection_counter - 1)
            
            # SADECE ART ARDA min_detections KERE TESPÝT EDÝLÝRSE ENGELLE
            if self.detection_counter >= self.min_detections:
                self.security_breach = True
                print("?? GUVENLIK IHLALI ONAYLANDI!")
                return "BLOCK_SCREEN"
            
            return "CLEAR"
            
        except Exception as e:
            print(f"? Guvenlik kontrolu hatasi: {e}")
            return "CLEAR"  # Hata durumunda engelleme
    
    def start_monitoring(self):
        """Kamera izlemeyi baslat"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("?? Kamera izleme baslatildi")
    
    def stop_monitoring(self):
        """Kamera izlemeyi durdur"""
        self.monitoring_active = False
        self.security_breach = False
        self.detection_counter = 0
        print("?? Kamera izleme durduruldu")
    
    def _monitor_loop(self):
        """Arka plan izleme dongusu"""
        cap = None
        try:
            cap = cv2.VideoCapture(0)
            
            while self.monitoring_active:
                ret, frame = cap.read()
                if ret:
                    self.monitor_security(frame)
                
                time.sleep(0.5)  # 0.5 saniyede bir kontrol
                
        except Exception as e:
            print(f"? Izleme dongusu hatasi: {e}")
        finally:
            if cap is not None:
                cap.release()

# Singleton instance
security_detector = SecurityDetector()