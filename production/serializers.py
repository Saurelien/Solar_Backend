from rest_framework import serializers
from .models import ProductionEntry
from django.contrib.auth.models import User

class ProductionEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductionEntry
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']