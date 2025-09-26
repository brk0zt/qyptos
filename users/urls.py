from django.urls import path
from .views import SignupView, LoginView, ProfileView, LogoutView
from . import views

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path('api/auth/login', views.login_view, name='login'),
    path("login/", LoginView.as_view(), name="login"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("logout/", LogoutView.as_view(), name="logout"),

]
