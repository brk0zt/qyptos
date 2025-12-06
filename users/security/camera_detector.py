# -*- coding: utf-8 -*-
# -*- coding: cp1254 -*-
import cv2
import numpy as np
import threading
import time
from django.conf import settings
import os

class AdvancedCameraDetector:
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.is_monitoring = False
        self.security_breach = False
        self.no_face_count = 0
        self.start_time = 0
        self.max_no_face_frames = 30  # 1 saniye (30 fps)
        
    def multi_method_lens_detection(self, frame):
        """Cok katmanli lens tespiti"""
        methods = [
            self.hough_circle_detection,
            self.bright_spot_analysis,
            self.contour_based_detection,
            self.reflection_pattern_analysis
        ]
        
        detection_scores = []
        for method in methods:
            try:
                score = method(frame)
                detection_scores.append(score)
            except Exception as e:
                detection_scores.append(0)
        
        # Aðýrlýklý ortalama ile karar
        weights = [0.3, 0.25, 0.3, 0.15]
        final_score = sum(s * w for s, w in zip(detection_scores, weights))
        
        return final_score > 0.6

    def hough_circle_detection(self, frame):
        """Hough Circle ile dairesel lens tespiti"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.medianBlur(gray, 5)
            
            # minRadius: 5'ten 15'e çýkardýk. Sadece büyük ve belirgin çemberler yakalanacak.
            circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1, 20,
                                     param1=50, param2=80, 
                                     minRadius=35, maxRadius=60) 
            return len(circles[0]) if circles is not None else 0
        except:
            return 0

    def bright_spot_analysis(self, frame):
        """Parlak nokta analizi ile lens yansimasi tespiti"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Eþiði 200'den 220'ye çýkardýk: Sadece en parlak yansýmalarý yakalamalý.
            _, bright_mask = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY) 
            
            # Morfolojik iþlemler
            kernel = np.ones((3,3), np.uint8)
            bright_mask = cv2.morphologyEx(bright_mask, cv2.MORPH_OPEN, kernel)
            
            bright_pixels = cv2.countNonZero(bright_mask)
            total_pixels = frame.shape[0] * frame.shape[1]
            
            # Oraný %1'den (%0.01) %0.5'e (%0.005) düþürdük: Parlak noktanýn küçük olmasý gerektiðini varsayýyoruz.
            return bright_pixels / total_pixels > 0.0005 
        except:
            return 0

    def contour_based_detection(self, frame):
        """Kontur analizi ile lens tespiti"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            lens_like_contours = 0
            for contour in contours:
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    # Dairesellik aralýðýný daralttýk (0.7-1.2'den 0.8-1.1'e)
                    if 0.8 < circularity < 1.1 and 50 < area < 1000:
                        lens_like_contours += 1
            
            return lens_like_contours > 0
        except:
            return 0
            for contour in contours:
                area = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                
                if perimeter > 0:
                    circularity = 4 * np.pi * area / (perimeter * perimeter)
                    # Dairesellik - lensler genelde daireseldir
                    if 0.7 < circularity < 1.2 and 50 < area < 1000:
                        lens_like_contours += 1
            
            return lens_like_contours > 0

    def reflection_pattern_analysis(self, frame):
        """Yansima deseni analizi"""
        try:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            saturation = hsv[:,:,1]
            value = hsv[:,:,2]
            
            high_sat = cv2.countNonZero(cv2.inRange(saturation, 50, 255))
            high_val = cv2.countNonZero(cv2.inRange(value, 200, 255))
            
            total_pixels = frame.shape[0] * frame.shape[1]
            
            return (high_sat / total_pixels > 0.05) and (high_val / total_pixels > 0.05)
        except:
            return 0

    def detect_faces(self, frame):
        """Yuz tespiti"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            self.max_no_face_frames = 90
            return len(faces) > 0
        except:
            return False

    def monitor_security(self, frame):
        """Guvenlik izleme sistemi"""
        # 1. Lens tespiti
        lens_detected = self.multi_method_lens_detection(frame)
        
        # 2. Yüz tespiti
        face_detected = self.detect_faces(frame)
        
        # 3. Güvenlik mantýðý
        if lens_detected:
            self.security_breach = True
            return "BLOCK_SCREEN"
        
        if not face_detected:
            self.no_face_count += 1
            if self.no_face_count >= self.max_no_face_frames:
                self.security_breach = True
                return "BLOCK_SCREEN"
        else:
            self.no_face_count = 0  # Reset
        
        return "SHOW_CONTENT"

    def start_monitoring(self):
        """Kamera izlemeyi baslat"""
        self.is_monitoring = True
        self.security_breach = False
        self.start_time = time.time()

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return False
        
        while self.is_monitoring:
            ret, frame = cap.read()
            if not ret:
                break
                
            security_status = self.monitor_security(frame)
            
            if security_status == "BLOCK_SCREEN":
                break
                
            time.sleep(0.1)  # 10 FPS
        
        cap.release()
        cv2.destroyAllWindows()
        return self.security_breach

    def stop_monitoring(self):
        """Kamera izlemeyi durdur"""
        self.is_monitoring = False

# Global detector instance
security_detector = AdvancedCameraDetector()
