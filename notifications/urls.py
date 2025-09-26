from django.urls import path
from .views import NotificationListView, NotificationMarkAsReadView
from .views import notification_list, mark_as_read, mark_all_as_read

urlpatterns = [
    path("", notification_list, name="notifications"),
    path("<int:pk>/read/", mark_as_read, name="mark_as_read"),
    path("read-all/", mark_all_as_read, name="mark_all_as_read"),
    path("", NotificationListView.as_view(), name="notification-list"),
    path('<int:pk>/mark-read/', NotificationMarkAsReadView.as_view(), name='mark-as-read'),
]

