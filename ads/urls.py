from django.urls import path
from . import views

urlpatterns = [
    path('serve/', views.serve_ad, name='ads-serve'),
    path('impression/', views.register_impression, name='ads-impression'),
    path('click/', views.register_click, name='ads-click'),
    path('my-earnings/', views.my_earnings, name='ads-my-earnings'),
    path('admin/list/', views.admin_ad_list, name='ads-admin-list'),
]
