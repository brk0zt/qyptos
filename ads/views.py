import random
from decimal import Decimal
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Ad, AdPlacement, AdImpression, AdClick, PublisherEarning, AdLog
from .serializers import AdSerializer, AdPlacementSerializer, PublisherEarningSerializer
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Max
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
import csv
from io import BytesIO
from django.http import HttpResponse
from reportlab.pdfgen import canvas

class AdView(APIView):
    def get(self, request):
        ads = Ad.objects.filter(is_active=True)
        if not ads.exists():
            return Response({"message": "No ads available"}, status=404)

        ad = random.choice(ads)  

        AdLog.objects.create(ad=ad, user=request.user if request.user.is_authenticated else None, event_type="view")
        serializer = AdSerializer(ad)
        return Response(serializer.data)

class AdClickView(APIView):  
    permission_classes = [IsAuthenticated]

    def post(self, request, ad_id):
        ad = get_object_or_404(Ad, id=ad_id)
        AdLog.objects.create(ad=ad, user=request.user, event_type="click")
        return Response({"message": "Click logged"})

class AdReportView(APIView):  
    permission_classes = [IsAuthenticated]

    def get(self, request, ad_id):
        ad = get_object_or_404(Ad, id=ad_id)

        logs = AdLog.objects.filter(ad=ad)
        views = logs.filter(event_type="view").count()
        clicks = logs.filter(event_type="click").count()

        last_view = logs.filter(event_type="view").aggregate(last=Max("created_at"))["last"]
        last_click = logs.filter(event_type="click").aggregate(last=Max("created_at"))["last"]

        def aggregate(interval):
            qs = (
                logs.annotate(period=interval("created_at"))
                .values("period", "event_type")
                .annotate(count=Count("id"))
                .order_by("period")
            )
            return list(qs)

        daily_stats = aggregate(TruncDate)
        weekly_stats = aggregate(TruncWeek)
        monthly_stats = aggregate(TruncMonth)

        detailed_logs = logs.select_related("user").order_by("-created_at")[:50]  # son 50

        return Response({
            "ad": ad.title,
            "views": views,
            "clicks": clicks,
            "last_view": last_view,
            "last_click": last_click,
            "stats": {
                "daily": daily_stats,
                "weekly": weekly_stats,
                "monthly": monthly_stats,
            },
            "logs": [
                {
                    "user": log.user.username if log.user else "Anonim",
                    "event_type": log.event_type,
                    "created_at": log.created_at
                }
                for log in detailed_logs
            ]
        })

def aggregate_stats(logs, interval):
    qs = (
        logs.annotate(period=interval("created_at"))
        .values("period", "event_type")
        .annotate(count=Count("id"))
        .order_by("period")
    )
    return list(qs)

class AdReportExportCSV(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, ad_id):
        ad = get_object_or_404(Ad, id=ad_id)
        logs = AdLog.objects.filter(ad=ad).order_by("-created_at")

        # Özet istatistikler
        daily = aggregate_stats(logs, TruncDate)
        weekly = aggregate_stats(logs, TruncWeek)
        monthly = aggregate_stats(logs, TruncMonth)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{ad.title}_report.csv"'

        writer = csv.writer(response)
        writer.writerow([f"Reklam Raporu: {ad.title}"])
        writer.writerow([])

        writer.writerow(["--- Gunluk Istatistikler ---"])
        writer.writerow(["Tarih", "Olay", "Sayi"])
        for row in daily:
            writer.writerow([row["period"], row["event_type"], row["count"]])

        writer.writerow([])
        writer.writerow(["--- Haftalik Istatistikler ---"])
        writer.writerow(["Hafta", "Olay", "Sayi"])
        for row in weekly:
            writer.writerow([row["period"], row["event_type"], row["count"]])

        writer.writerow([])
        writer.writerow(["--- Aylik Istatistikler ---"])
        writer.writerow(["Ay", "Olay", "Sayi"])
        for row in monthly:
            writer.writerow([row["period"], row["event_type"], row["count"]])

        writer.writerow([])
        writer.writerow(["--- Detayli Loglar ---"])
        writer.writerow(["Kullanici", "Olay", "Tarih"])
        for log in logs:
            writer.writerow([
                log.user.username if log.user else "Anonim",
                "Goruntuleme" if log.event_type == "view" else "Tiklama",
                log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            ])

        return response

class AdReportExportPDF(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, ad_id):
        ad = get_object_or_404(Ad, id=ad_id)
        logs = AdLog.objects.filter(ad=ad).order_by("-created_at")

        daily = aggregate_stats(logs, TruncDate)
        weekly = aggregate_stats(logs, TruncWeek)
        monthly = aggregate_stats(logs, TruncMonth)

        buffer = BytesIO()
        p = canvas.Canvas(buffer)
        p.setFont("Helvetica", 12)

        p.drawString(100, 800, f"Reklam Raporu: {ad.title}")
        p.drawString(100, 780, f"Toplam Goruntuleme: {logs.filter(event_type='view').count()}")
        p.drawString(100, 760, f"Toplam Tiklama: {logs.filter(event_type='click').count()}")

        y = 730
        p.drawString(100, y, "--- Gunluk Istatistikler ---")
        y -= 20
        for row in daily:
            p.drawString(100, y, f"{row['period']} - {row['event_type']} - {row['count']}")
            y -= 20

        y -= 20
        p.drawString(100, y, "--- Haftalik Istatistikler ---")
        y -= 20
        for row in weekly:
            p.drawString(100, y, f"{row['period']} - {row['event_type']} - {row['count']}")
            y -= 20

        y -= 20
        p.drawString(100, y, "--- Aylik Istatistikler ---")
        y -= 20
        for row in monthly:
            p.drawString(100, y, f"{row['period']} - {row['event_type']} - {row['count']}")
            y -= 20

        y -= 20
        p.drawString(100, y, "--- Detayli Loglar ---")
        y -= 20
        for log in logs:
            line = f"{log.user.username if log.user else 'Anonim'} - {log.event_type.upper()} - {log.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
            p.drawString(100, y, line)
            y -= 20
            if y < 50:
                p.showPage()
                y = 800

        p.save()
        buffer.seek(0)

        response = HttpResponse(buffer, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{ad.title}_report.pdf"'
        return response

# ... Diğer fonksiyonlar aynı kalacak ...
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