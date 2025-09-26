import random
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Ad, UserEarning, GroupFile
from .serializers import AdSerializer, UserEarningSerializer


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_random_ad(request):
    ads = Ad.objects.filter(is_active=True)
    if not ads.exists():
        return Response({"message": "No ads available"})
    ad = random.choice(ads)
    serializer = AdSerializer(ad)
    return Response(serializer.data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def register_view_and_reward(request):
    file_id = request.data.get("file_id")
    reward_amount = 0.05  # her izlenmede kazanç (örnek değer)

    try:
        file = GroupFile.objects.get(id=file_id)
    except GroupFile.DoesNotExist:
        return Response({"error": "File not found"}, status=404)

    # İçerik sahibine kazanç ekle
    earning, created = UserEarning.objects.get_or_create(user=uploader)
    earning.amount += reward_amount
    earning.save()

    return Response({
        "message": f"View registered. {uploader.username} earned {reward_amount}₺",
        "total_earning": earning.amount
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def my_earnings(request):
    earning, created = UserEarning.objects.get_or_create(user=request.user)
    serializer = UserEarningSerializer(earning)
    return Response(serializer.data)

