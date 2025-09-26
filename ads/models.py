from django.db import models
from django.conf import settings
from decimal import Decimal

class Ad(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='ads/', null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    cpm = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('1.00'))  # cost per 1000 impressions in platform currency
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                              help_text='Optional: who created/uploaded the ad')

    def __str__(self):
        return f"Ad: {self.title} (CPM={self.cpm})"

class AdPlacement(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    def __str__(self):
        return self.name

class AdImpression(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='impressions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    placement = models.ForeignKey(AdPlacement, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=100, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

class AdClick(models.Model):
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='clicks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=100, blank=True, null=True)

class PublisherEarning(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='publisher_earnings')
    amount = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.user.username} - {self.amount}"
