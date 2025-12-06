# -*- coding: utf-8 -*-
import os 
from rest_framework import serializers
from django.utils import timesince
from django.urls import reverse
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
    file = FileSerializer(read_only=True)
    secure_url = serializers.SerializerMethodField()

    class Meta:
        model = FileShare
        fields = ['id', 'token', 'file', 'secure_url', 'view_count', 'max_views', 'is_revoked', 'created_at']

    def get_secure_url(self, obj):
        request = self.context.get('request')
        
        # Eğer iptal edilmişse veya hak dolmuşsa link verme
        if obj.is_revoked or (obj.max_views > 0 and obj.view_count >= obj.max_views):
            return None
            
        try:
            # Token ile güvenli link oluştur
            return request.build_absolute_uri(reverse('secure_media_view', args=[obj.token]))
        except Exception:
            return None

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        
        # Hangi sayfada olduğumuzu kontrol et
        is_list_view = False
        if request and request.resolver_match:
            # Eğer arama veya trend listesindeysek
            if request.resolver_match.url_name in ['search_public_files', 'trending_files', 'search']:
                is_list_view = True

        # Eğer kısıtlı/tek gösterimlik bir dosya ise
        if instance.max_views > 0:
            if 'file' in ret:
                secure_link = self.get_secure_url(instance)
                
                if is_list_view:
                    # 🛑 LİSTE GÖRÜNÜMÜNDE RESMİ GİZLE (Thumbnail hakkını yemesin)
                    # Frontend burada "Kilit" ikonu veya placeholder gösterebilir
                    ret['file']['file'] = None 
                    ret['file']['url'] = None
                else:
                    # ✅ DETAY SAYFASINDA (veya paylaşım sayfasında) GÜVENLİ LİNKİ VER
                    # Burası /share/TOKEN/ sayfası için çalışır
                    ret['file']['file'] = secure_link
                    ret['file']['url'] = secure_link
        
        return ret