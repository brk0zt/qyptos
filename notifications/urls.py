from django.urls import path
from .views import notification_list, mark_as_read, mark_all_as_read
from . import views
from .views import NotificationListView, NotificationMarkReadView

urlpatterns = [
    path("", notification_list, name="notifications"),
    path("<int:pk>/read/", mark_as_read, name="mark_as_read"),
    path("read-all/", mark_all_as_read, name="mark_all_as_read"),
    path('<int:notification_id>/read/', views.mark_as_read, name='notification-mark-read'),
    path('', views.notification_list, name='notification-list'),
    path("", NotificationListView.as_view(), name="notification_list"),
    path("mark-read/", NotificationMarkReadView.as_view(), name="notification_mark_read"),
]

