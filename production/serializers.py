from rest_framework import serializers
from .models import ProductionData, WeatherCredential
from django.contrib.auth.models import User


class ProductionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionData
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']



class WeatherCredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherCredential
        fields = ['api_key']