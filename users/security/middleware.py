# -*- coding: utf-8 -*-
"""
Security Middleware - Tek Gösterimlik Medya Koruması
"""

from django.http import JsonResponse
from django.shortcuts import render
from users.security.camera_detector import security_detector
from django.utils.deprecation import MiddlewareMixin

class CameraSecurityMiddleware(MiddlewareMixin):
    """
    Güvenlik middleware'i - Şüpheli aktiviteleri tespit eder
    """
    
    def process_request(self, request):
        """
        İstek işlenmeden önce kontrol et
        """
        # Güvenlik kontrolü yap (sadece /share/ endpoint'lerinde)
        if '/share/' in request.path:
            # monitoring_active kontrolü
            if hasattr(security_detector, 'monitoring_active') and security_detector.monitoring_active:
                # if security_detector.security_breach:
                    # Güvenlik ihlali tespit edildi
                 #   return JsonResponse({
                  #      'error': 'Güvenlik ihlali tespit edildi',
                   #     'reason': 'CAMERA_DETECTED'
                   # }, status=403)
                pass
            
            # Şüpheli user agent kontrolü
            user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
            suspicious_agents = ['bot', 'crawler', 'scraper', 'screenshot', 'headless']
            
          #  if any(agent in user_agent for agent in suspicious_agents):
           #     return JsonResponse({
            #        'error': 'Şüpheli istek tespit edildi',
             #       'reason': 'SUSPICIOUS_USER_AGENT'
              #  }, status=403)
        
        return None