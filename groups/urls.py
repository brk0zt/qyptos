from django.urls import path
from .views import (
    FileDownloadView, FileDetailView, FileReportExportPDF, FileReportExportCSV,
    GroupListView, GroupCreateView, GroupJoinView, GroupLeaveView,
    FileUploadView, CommentCreateView, FileReportView,
    UserProfileView, GroupAuthCheckView, GroupFilesView, FileCommentsView, 
    CommentListView, CommentReplyView, GroupInviteView, GroupJoinByInviteView, 
    GroupInviteByCodeView, GroupInvitationsView, PublicFileSearchView, SearchSuggestionsView, 
    SearchStatsView, PopularSearchesView, websocket_debug
)

urlpatterns = [
    # Kullanýcý URL'leri
    path("users/me/", UserProfileView.as_view(), name="user_profile"),
    
    # Grup URL'leri
    path("groups/", GroupListView.as_view(), name="group_list"),
    path("groups/create/", GroupCreateView.as_view(), name="group_create"),
    path("groups/<int:group_id>/join/", GroupJoinView.as_view(), name="group_join"),
    path("groups/<int:group_id>/leave/", GroupLeaveView.as_view(), name="group_leave"),
    path("groups/<int:group_id>/check-auth/", GroupAuthCheckView.as_view(), name="group_auth_check"),
    path("groups/<int:group_id>/files/", GroupFilesView.as_view(), name="group_files"),
    path("groups/<int:group_id>/invite/", GroupInviteView.as_view(), name="group_invite"),
    path("groups/invite/<str:token>/join/", GroupJoinByInviteView.as_view(), name="group_join_by_invite"),
    path("groups/join-by-code/", GroupInviteByCodeView.as_view(), name="group_join_by_code"),
    path("groups/<int:group_id>/invitations/", GroupInvitationsView.as_view(), name="group_invitations"),
    
    # Dosya URL'leri
    path("groups/<int:group_id>/upload/", FileUploadView.as_view(), name="file_upload"),
    path("files/<int:file_id>/download/", FileDownloadView.as_view(), name="file_download"),
    path("files/<int:file_id>/", FileDetailView.as_view(), name="file_detail"),
    path("files/<int:file_id>/comment/", CommentCreateView.as_view(), name="file_comment"),
    path("files/<int:file_id>/comments/", CommentListView.as_view(), name="comment_list"),
    path("files/<int:file_id>/comments/", FileCommentsView.as_view(), name="file_comments"),
    path("comments/<int:comment_id>/reply/", CommentReplyView.as_view(), name="comment_reply"),
    path("files/<int:file_id>/report/", FileReportView.as_view(), name="file_report"),
    path("files/<int:file_id>/report/pdf/", FileReportExportPDF.as_view(), name="file_report_pdf"),
    path("files/<int:file_id>/report/csv/", FileReportExportCSV.as_view(), name="file_report_csv"),
     path("search/public-files/", PublicFileSearchView.as_view(), name="public_file_search"),
    path("search/suggestions/", SearchSuggestionsView.as_view(), name="search_suggestions"),
    path("search/stats/", SearchStatsView.as_view(), name="search_stats"),
    path("search/popular/", PopularSearchesView.as_view(), name="popular_searches"),

    path('websocket-debug/', websocket_debug, name='websocket_debug'),
]