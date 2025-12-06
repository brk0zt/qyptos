from django.urls import path
from . import views
from .views import AdView, AdClickView, AdReportView, AdReportExportCSV, AdReportExportPDF

urlpatterns = [
    path('serve/', views.serve_ad, name='ads-serve'),
    path('impression/', views.register_impression, name='ads-impression'),
    path('click/', views.register_click, name='ads-click'),
    path('my-earnings/', views.my_earnings, name='ads-my-earnings'),
    path('admin/list/', views.admin_ad_list, name='ads-admin-list'),
    path("", AdView.as_view(), name="get_ad"),
    path("<int:ad_id>/click/", AdClickView.as_view(), name="ad_click"),
    path("<int:ad_id>/report/", AdReportView.as_view(), name="ad_report"),
    path("<int:ad_id>/report/csv/", AdReportExportCSV.as_view(), name="ad_report_csv"),
    path("<int:ad_id>/report/pdf/", AdReportExportPDF.as_view(), name="ad_report_pdf"),
]
