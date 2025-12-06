# -*- coding: utf-8 -*-
import os 
from rest_framework import serializers
from django.utils import timesince
from .models import File, CloudGroup, GroupFile, FileComment, GroupInvite, GroupFeed, Ad, UserEarning, SecureLink, MediaFile, FileShare  
from django.utils import timezone
from datetime import timedelta

class MediaFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaFile
        fields = ["id", "file", "uploader", "single_view", "consumed_by"]
        read_only_fields = ["uploader", "consumed_by"]


class SecureLinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecureLink
        fields = ["id", "token", "file", "expires_at", "max_uses", "used_count"]

class FileSerializer(serializers.ModelSerializer):
    # ✅ FRONTEND'İN İSTEDİĞİ YENİ ALANLAR
    created_by_username = serializers.SerializerMethodField()
    upload_time_ago = serializers.SerializerMethodField()
    is_password_protected = serializers.SerializerMethodField() # Frontend Rozet
    
    # Kullanıcının tanımladığı alanlar
    file_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()
    share_url = serializers.SerializerMethodField() # Frontend'in tıkladığı ana URL

    class Meta:
        model = File
        fields = [
            'id', 'file', 'file_url', 'share_url', 'file_name', 
            'uploaded_at', 'one_time_view', 'has_been_viewed', 
            'view_token', 'is_public', 'file_size', 'file_size_mb', 
            'view_duration', 'can_download', 'created_by_username', 
            'upload_time_ago', 'is_password_protected' # Tüm gerekli alanlar burada
        ]
        read_only_fields = [
            'uploaded_at', 'has_been_viewed', 'view_token', 
            'file_size', 'file_url', 'share_url', 'file_name', 
            'file_size_mb', 'created_by_username', 'upload_time_ago',
            'is_password_protected'
        ]
    
    # --- 500 HATASI ÇÖZÜMLERİ ve YENİ METODLAR ---

    # Düzeltme: Method adı 'can_download' field'ı ile eşleşmeli.
    def get_can_download(self, obj):
        # Varsayalım ki 'can_download' doğrudan File modelinde bir alandır
        return obj.can_download
        
    # YENİ ALAN: Dosya Adı (os import'u ve hata kontrolü ile)
    def get_file_name(self, obj):
        try:
            # obj.file, FileField'ınız olmalı
            return os.path.basename(obj.file.name) if obj.file else "Dosya Adı Yok"
        except Exception:
            # Hata oluşursa 500 hatası vermemek için güvenli dönüş
            return "HATA"

    # YENİ ALAN: Dosya URL'si (Sınıf içinde olmalı ve hata kontrolü ile)
    def get_file_url(self, obj):
        try:
            request = self.context.get('request')
            # obj.file.url, FileField'ın URL'si
            url = request.build_absolute_uri(obj.file.url) if request and obj.file else None
            return url
        except Exception:
            return None

    # YENİ ALAN: Paylaşım/Görüntüleme URL'si (Frontend'in tıklayacağı link)
    def get_share_url(self, obj):
        # Varsayalım ki, tek gösterimlik/şifreli durumlar için Token kullanılıyor
        if obj.view_token:
            request = self.context.get('request')
            # Token ile paylaşım linki oluşturulmalı (Sizin urls.py'deki 'share-file' view'ini kullanıyor olabilir)
            return request.build_absolute_uri(f'/share/{obj.view_token}/')
        
        # Standart dosya URL'sini döndür
        return self.get_file_url(obj)
        
    # YENİ ALAN: Yükleyen Kullanıcı Adı
    def get_created_by_username(self, obj):
        # Varsayalım ki dosyanın sahibi 'owner' alanında tutuluyor.
        return obj.owner.username if hasattr(obj, 'owner') and obj.owner else 'Anonim'

    # YENİ ALAN: Yükleme Zamanı
    def get_upload_time_ago(self, obj):
        # Varsayalım ki dosyanın oluşturulma zamanı 'uploaded_at' alanında tutuluyor.
        if obj.uploaded_at:
            return f"{timesince.timesince(obj.uploaded_at)} önce"
        return "Tarih Yok"

    # YENİ ALAN: Şifreli Rozeti
    def get_is_password_protected(self, obj):
        # Modelde şifreli olup olmadığını kontrol eden bir alan (örn. 'password' veya 'password_hash') varsayıyoruz.
        # Eğer modelinizde böyle bir alan varsa True/False döndürün.
        return bool(obj.password_hash) if hasattr(obj, 'password_hash') else False # Varsayımsal Kontrol
        
    # Mevcut method (Hata kontrolü eklenmiş)
    def get_file_size_mb(self, obj):
        try:
            size_bytes = 0
            if obj.file_size and str(obj.file_size).isdigit():
                size_bytes = int(obj.file_size)
            elif obj.file and hasattr(obj.file, 'size'):
                size_bytes = obj.file.size
            
            return round(size_bytes / (1024 * 1024), 2)
        except Exception:
            return 0

class CloudGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CloudGroup
        fields = ['id','name','owner','invite_token','is_public']

class GroupFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupFile
        fields = ['id','group','file','uploader','uploaded_at','one_time_view','has_been_viewed','view_token','is_public']
        read_only_fields = ['uploader','uploaded_at','has_been_viewed','view_token']

class FileCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FileComment
        fields = ['id','file','author','content','created_at']
        read_only_fields = ['author','created_at']

class GroupInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroupInvite
        fields = ["id", "group", "email", "invited_by", "created_at", "accepted"]
        read_only_fields = ["invited_by", "created_at", "accepted"]

class GroupFeedSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    group = serializers.StringRelatedField()
    related_file = serializers.StringRelatedField()

    class Meta:
        model = GroupFeed
        fields = ["id", "group", "user", "feed_type", "content", "related_file", "created_at"]

class AdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = ["id", "title", "image", "link", "is_active"]

class UserEarningSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = UserEarning
        fields = ["id", "user", "amount", "updated_at"]

class FileShareSerializer(serializers.ModelSerializer):
    share_url = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()
    created_by_username = serializers.SerializerMethodField()
    file_type = serializers.SerializerMethodField()
    trend_score = serializers.FloatField(read_only=True)
    upload_time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = FileShare
        fields = [
            'id', 'file', 'share_type', 'token', 'share_url', 
            'file_name', 'created_at', 'expires_at', 'max_views', 
            'view_count', 'password', 'created_by_username',
            'file_type' , 'trend_score', 'upload_time_ago'
        ]
        read_only_fields = ['token', 'view_count', 'created_at', 'trend_score']
    
    def get_share_url(self, obj):
        request = self.context.get('request')
    
    # 1. Öncelik: Dosyanın view_token'ı varsa onu kullan
        if obj.view_token:
        # Token ile paylaşım linkini oluştur. (Sizin urls.py'nizdeki 'share/<uuid:token>/' yolu için)
            try:
            # Token'ı URL'ye doğrudan ekle
                return request.build_absolute_uri(f'/share/{obj.view_token}/')
            except Exception:
            # URL oluşturma hatası olursa devam et (500 hatasını engellemek için)
                pass

    # 2. Öncelik: Eğer dosya herkese açık (is_public=True) ise, genel dosya detay view'ine yönlendir.
    # Bu, arama sonuçlarında görünen public dosyalar için en güvenli yoldur.
        elif hasattr(obj, 'is_public') and obj.is_public:
            try:
            # Varsayalım ki, 'files/<int:pk>/' adında bir detay view'iniz var.
            # VEYA direk dosya URL'sine yönlendir
                return self.get_file_url(obj)
            
            except Exception:
                pass

    # Hiçbiri yoksa, null döndür (veya sadece file_url'yi dene)
        return self.get_file_url(obj) if hasattr(self, 'get_file_url') else None
    
    def get_created_by_username(self, obj):
        return obj.created_by.username if obj.created_by else None
    
    def get_file_type(self, obj):
        if obj.file and hasattr(obj.file, 'file'):
            filename = obj.file.file.name.lower()
            if any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                return 'image'
            elif any(filename.endswith(ext) for ext in ['.mp4', '.avi', '.mov']):
                return 'video'
            elif any(filename.endswith(ext) for ext in ['.mp3', '.wav', '.ogg']):
                return 'audio'
            elif any(filename.endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt']):
                return 'document'
            return 'other'
        return 'other'

    def get_upload_time_ago(self, obj):
        # Yüklenme zamanını "X dakika önce", "Y gün önce" formatında döndürür
        now = timezone.now()
        diff = now - obj.created_at
        if diff < timedelta(minutes=1):
            return "Simdi"
        elif diff < timedelta(hours=1):
            return f"{diff.seconds // 60} dakika once"
        elif diff < timedelta(days=1):
            return f"{diff.seconds // 3600} saat once"
        elif diff < timedelta(days=30):
            return f"{diff.days} gun once"
        else:
            return obj.created_at.strftime("%d %b %Y")
            
    def get_file_name(self, obj):
        return os.path.basename(obj.file.file.name) if obj.file and obj.file.file else 'Bilinmeyen Dosya'
