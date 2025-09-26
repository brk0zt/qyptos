from django.urls import path, include
from .views import (
    create_secure_link, download_with_token, send_invite, accept_invite,
    FileUploadListView, FileDetailView, FileOneTimeView,
    CloudGroupCreateView, CloudGroupJoinView, CloudGroupListView,
    CloudGroupDetailView, GroupFileUploadView, GroupFileCommentCreateView,
    range_download_view, register_device, access_file
)
from .ad_views import (
    get_random_ad, register_view_and_reward, my_earnings
)
from rest_framework.routers import DefaultRouter
from .views import MediaFileViewSet
from . import views

router = DefaultRouter()
router.register(r"media-files", MediaFileViewSet, basename="media-files")

urlpatterns = [
    # Views from views.py
    path("auth/", include("users.urls")),
    path('secure-link/create/<uuid:file_id>/', create_secure_link, name='create_secure_link'),
    path('secure-link/download/<str:token>/', download_with_token, name='download_with_token'),
    path('send-invite/', send_invite, name='send_invite'),
    path('accept-invite/', accept_invite, name='accept_invite'),
    path('files/', FileUploadListView.as_view(), name='file_upload_list'),
    path('files/<int:pk>/', FileDetailView.as_view(), name='file_detail'),
    path('files/one-time-view/<str:token>/', FileOneTimeView.as_view(), name='file_one_time_view'),
    path('groups/', CloudGroupCreateView.as_view(), name='group_create'),
    path('groups/list/', CloudGroupListView.as_view(), name='group_list'),
    path('groups/join/', CloudGroupJoinView.as_view(), name='group_join'),
    path('groups/<int:pk>/', CloudGroupDetailView.as_view(), name='group_detail'),
    path('groups/<int:group_id>/files/', GroupFileUploadView.as_view(), name='group_file_upload_list'),
    path('groups/files/<int:file_id>/comments/', GroupFileCommentCreateView.as_view(), name='group_file_comment'),
    path('download/<str:file_name>/', range_download_view, name='range_download'),
    path('devices/register/', register_device, name='register_device'),
    path('devices/access-file/<str:file_name>/', access_file, name='access_file'),

    # Views from ad_views.py
    path('ads/random/', get_random_ad, name='get_random_ad'),
    path('ads/reward/', register_view_and_reward, name='register_view_and_reward'),
    path('ads/my-earnings/', my_earnings, name='my_earnings'),
    path("", include(router.urls)),
]