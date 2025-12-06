from rest_framework import serializers
from .models import Ad, AdPlacement, AdImpression, AdClick, PublisherEarning

class AdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = ['id','title','media','link','cpm','is_active','created_at']

class AdPlacementSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdPlacement
        fields = ['id','name','description']

class AdImpressionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdImpression
        fields = ['id','ad','user','placement','created_at']

class AdClickSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdClick
        fields = ['id','ad','user','created_at']

class PublisherEarningSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    class Meta:
        model = PublisherEarning
        fields = ['id','user','amount','updated_at']
