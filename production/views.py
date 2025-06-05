from rest_framework import viewsets, permissions
from .models import ProductionEntry
from .serializers import ProductionEntrySerializer, UserSerializer
from django.contrib.auth.models import User

class ProductionEntryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ProductionEntry.objects.order_by('-timestamp')[:100]  # limit to latest 100
    serializer_class = ProductionEntrySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]
