# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404
from groups.models import GroupFile
from groups.serializers import GroupFileSerializer, CommentSerializer
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from chat.models import UserStatus
from .models import CustomUser
from chat.serializers import UserStatusSerializer
from .serializers import UserSerializer 
from django.contrib.auth import get_user_model
from files.models import (
    File, CloudGroup, GroupFile, FileComment, SecureLink, FileShare
)
from .models import Device
from files.serializers import FileShareSerializer
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes

User = get_user_model()

class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            username = request.data.get('username')
            email = request.data.get('email')
            password = request.data.get('password')
            
            # CustomUser üzerinde kontrol et
            if CustomUser.objects.filter(username=username).exists():
                return Response({
                    'success': False,
                    'message': 'Username already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
                
            if CustomUser.objects.filter(email=email).exists():
                return Response({
                    'success': False,
                    'message': 'Email already exists'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # CustomUser ile yeni kullanýcý oluþtur
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # JWT token oluþtur
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'success': True,
                'message': 'User created successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                },
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            # React'ten email geliyor
            email = request.data.get("email")
            password = request.data.get("password")

            # CustomUser üzerinde email ile kullanýcý bul
            try:
                user = CustomUser.objects.get(email=email)
                # authenticate için username kullan
                user = authenticate(request, username=user.username, password=password)
            except CustomUser.DoesNotExist:
                return Response(
                    {"success": False, "message": "Invalid email or password"},
                    status=status.HTTP_401_UNAUTHORIZED
                )

            if user is not None:
                refresh = RefreshToken.for_user(user)
                return Response({
                    "success": True,
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
                    {"success": False, "message": "Invalid email or password"},
                    status=status.HTTP_401_UNAUTHORIZED
                )
                
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        })

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id': user.id,
            'username': user.username,
            'email': user.email
        })

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # JWT token'ý blacklist'e ekle
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            return Response({
                "success": True,
                "message": "Successfully logged out"
            })
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class FileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        file = get_object_or_404(GroupFile, id=file_id)
        file_data = GroupFileSerializer(file).data

        # Tek seferlik görsel/pdf dosyalarý için view URL ekle
        if file.one_time_view and not file.has_been_viewed:
            file_data["view_url"] = f"http://127.0.0.1:8001/groups/files/{file.id}/download/"
        else:
            file_data["view_url"] = None

        comments = CommentSerializer(file.comments.all().order_by("-created_at"), many=True).data
        return Response({"file": file_data, "comments": comments})

    class UserStatusView(APIView):
        permission_classes = [IsAuthenticated]

    def get(self, request):
        user_status, created = UserStatus.objects.get_or_create(user=request.user)
        serializer = UserStatusSerializer(user_status)
        return Response(serializer.data)

    def post(self, request):
        user_status, created = UserStatus.objects.get_or_create(user=request.user)
        user_status.is_online = request.data.get('is_online', user_status.is_online)
        user_status.save()
        serializer = UserStatusSerializer(user_status)
        return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny]) # Arama motoru herkese açýk olabilir
def search_public_files_view(request):
    """
    Herkese acik olarak paylasilan dosyalari arama sorgusuna gore filtreler.
    Sadece 'public' (Herkese Acik) paylasimlari dondurur.
    """
    
    query = request.query_params.get('q', None)
    
    if not query:
        return Response({
            'fileshares': [], 
            'message': 'Lutfen bir arama kelimesi girin.'
        }, status=200)

    # Sadece 'public' (Herkese Açýk) paylaþýmlarý filtrele
    public_shares_queryset = FileShare.objects.filter(share_type='public', file__isnull=False)
    
    # Arama Kriterleri: Dosya adý VEYA paylaþýmý oluþturan kullanýcý adý
    search_criteria = Q(file__file__icontains=query) | Q(created_by__username__icontains=query)
    
    # Kriterlere uyan paylaþýmlarý filtrele
    search_results = public_shares_queryset.filter(search_criteria).distinct()
    
    # Serizializer'ý kullanarak veriyi formatla
    # Dikkat: `from .serializers import FileShareSerializer` yukarýda olduðundan emin olun.
    from .serializers import FileShareSerializer 
    
    serializer = FileShareSerializer(
        search_results, 
        many=True, 
        context={'request': request}
    )
    
    return Response({
        'fileshares': serializer.data, 
        'message': f"'{query}' icin {search_results.count()} sonuc bulundu."
    })
    