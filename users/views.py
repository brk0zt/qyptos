from rest_framework import generics, permissions
from .serializers import RegisterSerializer
from .models import CustomUser
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from rest_framework.permissions import AllowAny
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.views.decorators.http import require_http_methods

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()  # refresh token artýk geçersiz
            return Response({"message": "Basariyla cikis yapildi"}, status=200)
        except Exception as e:
            return Response({"error": "Gecersiz token"}, status=400)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email
        })

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)

        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Gecersiz kullanici adi veya sifre"},
                status=status.HTTP_401_UNAUTHORIZED
            )


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        if not username or not email or not password:
            return Response(
                {"error": "Tum alanlar zorunludur."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Bu kullanici adi zaten alinmis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "Bu e-posta adresi zaten kayitli."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.create(
            username=username,
            email=email,
            password=make_password(password),
        )

        # Yeni kullanýcýya otomatik token üret
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "message": "Kullanici basariyla olusturuldu",
                "user": {"id": user.id, "username": user.username, "email": user.email},
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


@csrf_exempt
@require_http_methods(["POST"])  # SADECE POST'A ÝZÝN VER
def login_view(request):
    print("=== LOGIN VIEW CALISTI ===")  # Debug için
    print("Method:", request.method)     # Hangi method geldi?
    print("Body:", request.body)         # Veriyi gör
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            
            print("Email:", email)
            print("Password:", password)
            
            # Basit bir test response'u döndür
            return JsonResponse({
                'success': True,
                'message': 'Login basarili!',
                'user': {'email': email}
            })
            
        except Exception as e:
            print("Error:", str(e))
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


