from django.urls import path
from .views import ChatThreadView, MessageListView, FileUploadView, DeleteMessageView, EditMessageView, UserListView
from . import consumers
from .views import MarkAsReadView
from .views import ToggleReactionView


websocket_urlpatterns = [
    path('ws/chat/<str:thread_id>/', consumers.ChatConsumer.as_asgi()),
    path('ws/presence/', consumers.PresenceConsumer.as_asgi()),
]

urlpatterns = [
    path("thread/<int:user_id>/", ChatThreadView.as_view(), name="chat_thread"),
    path("messages/<int:thread_id>/", MessageListView.as_view(), name="chat_messages"),
    path("upload/", FileUploadView.as_view(), name="chat_file_upload"),
    path("delete/<int:message_id>/", DeleteMessageView.as_view(), name="delete_message"),
    path("edit/<int:message_id>/", EditMessageView.as_view(), name="edit_message"),
    path("users/", UserListView.as_view(), name="user_list"),
    path("read/<int:message_id>/", MarkAsReadView.as_view(), name="mark_as_read"),
    path("reaction/<int:message_id>/", ToggleReactionView.as_view(), name="toggle_reaction"),

]

