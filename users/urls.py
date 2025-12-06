from django.urls import path
from .views import SignupView, LoginView, ProfileView, LogoutView
from . import views
from .views import CurrentUserView

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("users/me/", CurrentUserView.as_view(), name="current_user"),
    path('api/search/public/', views.search_public_files_view, name='search_public_files'),
]
