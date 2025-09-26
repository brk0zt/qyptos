import random
from decimal import Decimal
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Ad, AdPlacement, AdImpression, AdClick, PublisherEarning
from .serializers import AdSerializer, AdPlacementSerializer, PublisherEarningSerializer

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def serve_ad(request):
    placement_name = request.query_params.get('placement')
    qs = Ad.objects.filter(is_active=True)
    if placement_name:
        pass
    ad = random.choice(list(qs)) if qs.exists() else None
    if not ad:
        return Response({'detail':'no ads'}, status=status.HTTP_204_NO_CONTENT)
    return Response(AdSerializer(ad, context={'request':request}).data)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_impression(request):
    data = request.data
    ad_id = data.get('ad_id')
    placement = data.get('placement')
    try:
        ad = Ad.objects.get(id=ad_id, is_active=True)
    except Ad.DoesNotExist:
        return Response({'error':'invalid ad'}, status=status.HTTP_400_BAD_REQUEST)
    placement_obj = None
    if placement:
        placement_obj, _ = AdPlacement.objects.get_or_create(name=placement)
    ip = request.META.get('REMOTE_ADDR')
    ua = request.META.get('HTTP_USER_AGENT','')
    user = request.user if request.user.is_authenticated else None
    AdImpression.objects.create(ad=ad, user=user, placement=placement_obj, ip=ip, user_agent=ua)
    publisher_id = data.get('publisher_id')
    if publisher_id:
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            pub = User.objects.get(id=publisher_id)
            earning, _ = PublisherEarning.objects.get_or_create(user=pub)
            per_impression = (Decimal(ad.cpm) / Decimal('1000')) * Decimal('0.7')
            earning.amount += per_impression
            earning.save()
        except Exception:
            pass
    return Response({'detail':'impression recorded'})

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_click(request):
    data = request.data
    ad_id = data.get('ad_id')
    try:
        ad = Ad.objects.get(id=ad_id)
    except Ad.DoesNotExist:
        return Response({'error':'invalid ad'}, status=status.HTTP_400_BAD_REQUEST)
    ip = request.META.get('REMOTE_ADDR')
    user = request.user if request.user.is_authenticated else None
    AdClick.objects.create(ad=ad, user=user, ip=ip)
    return Response({'detail':'click recorded'})

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_earnings(request):
    earning, _ = PublisherEarning.objects.get_or_create(user=request.user)
    return Response(PublisherEarningSerializer(earning).data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def admin_ad_list(request):
    if not request.user.is_staff:
        return Response({'error':'forbidden'}, status=status.HTTP_403_FORBIDDEN)
    ads = Ad.objects.all()
    return Response(AdSerializer(ads, many=True).data)
