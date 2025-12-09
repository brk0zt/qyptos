
# urls.py - FIXED VERSION
from django.urls import path, include
from .views import (
    create_secure_link, download_with_token, send_invite, accept_invite,
    FileUploadListView, FileDetailView, FileOneTimeView, FilePreviewView,
    CloudGroupCreateView, CloudGroupJoinView, CloudGroupListView,
    CloudGroupDetailView, GroupFileUploadView, GroupFileCommentCreateView,
    range_download_view, register_device, access_file, trending_files, 
    trending_by_category
)
from .views import analyze_camera_frame, report_security_breach, SecureMediaView
from .views import FileShareViewSet, revoke_share
from .ad_views import (
    get_random_ad, register_view_and_reward, my_earnings
)
from .search_views import SearchView, search_view
from rest_framework.routers import DefaultRouter
from .views import MediaFileViewSet
from . import views

router = DefaultRouter()
router.register(r'fileshare', FileShareViewSet, basename='fileshare')
router.register(r'media', MediaFileViewSet, basename='media')

urlpatterns = [
    # File operations
    path('files/', FileUploadListView.as_view(), name='file_upload_list'),
    path('files/<int:pk>/', FileDetailView.as_view(), name='file_detail'),
    path('files/<int:pk>/preview/', FilePreviewView.as_view(), name='file_preview'),
    path('files/one-time-view/<uuid:token>/', FileOneTimeView.as_view(), name='file_one_time_view'),
    
    # Secure links
    path('secure-link/create/<int:file_id>/', create_secure_link, name='create_secure_link'),
    path('secure-link/download/<str:token>/', download_with_token, name='download_with_token'),
    
    # Group invites
    path('send-invite/', send_invite, name='send_invite'),
    path('accept-invite/', accept_invite, name='accept_invite'),
    
    # Groups
    path('groups/', CloudGroupCreateView.as_view(), name='group_create'),
    path('groups/list/', CloudGroupListView.as_view(), name='group_list'),
    path('groups/join/', CloudGroupJoinView.as_view(), name='group_join'),
    path('groups/<int:pk>/', CloudGroupDetailView.as_view(), name='group_detail'),
    path('groups/<int:group_id>/files/', GroupFileUploadView.as_view(), name='group_file_upload_list'),
    path('groups/files/<int:file_id>/comments/', GroupFileCommentCreateView.as_view(), name='group_file_comment'),
    
    # Device and download
    path('download/<str:file_name>/', range_download_view, name='range_download'),
    path('devices/register/', register_device, name='register_device'),
    path('devices/access-file/<str:file_name>/', access_file, name='access_file'),

    # Ads
    path('ads/random/', get_random_ad, name='get_random_ad'),
    path('ads/reward/', register_view_and_reward, name='register_view_and_reward'),
    path('ads/my-earnings/', my_earnings, name='my_earnings'),
    
    # Trending
    path('trending/', views.trending_files, name='trending_files'),

    path('api/search/public/', views.search_public_files_view, name='search_public_files'), # YENİ

    path('api/search/public/', views.search_public_files_view, name='search_public_files'), # YEN�


    # Search endpoints
    path('api/search/', SearchView.as_view(), name='search'),
    path('search/', search_view, name='search_alt'),


    # Güvenlik endpoint'leri
    path('api/security/analyze-frame/', analyze_camera_frame, name='analyze-frame'),
    path('api/security/report-breach/', report_security_breach, name='report-breach'),
    
    # Güvenli medya görüntüleme
    path('api/secure-media/<str:token>/', views.secure_media_view, name='secure_media_view'),

    # G�venlik endpoint'leri
    path('api/security/analyze-frame/', analyze_camera_frame, name='analyze-frame'),
    path('api/security/report-breach/', report_security_breach, name='report-breach'),
    
    # G�venli medya g�r�nt�leme
 

]