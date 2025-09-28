from django.urls import path
from .views import FileDownloadView, FileDetailView

urlpatterns = [
    path("files/<int:file_id>/download/", FileDownloadView.as_view(), name="file_download"),
    path("files/<int:file_id>/", FileDetailView.as_view(), name="file_detail"),
]
