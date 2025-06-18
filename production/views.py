from rest_framework import status, permissions, viewsets
from .models import ProductionData
from datetime import date
from growatt import Growatt
import traceback
from .models import GrowattCredential
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import ProductionDataSerializer
from django.contrib.auth.models import User
from rest_framework.permissions import IsAdminUser
from production.serializers import UserSerializer


class GrowattSyncView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email et mot de passe requis"}, status=400)

        try:
            api = Growatt()
            api.login(email, password)
            plant = api.get_plants()[0]
            plant_id = plant["id"]
            detail = api.get_plant(plant_id)

            # Stockage dans la base
            ProductionData.objects.update_or_create(
                user_email=email,
                date=date.today(),
                defaults={
                    "plant_id": plant_id,
                    "power_now": float(detail.get("nominalPower", 0)),
                    "energy_today": float(detail.get("eTotal", 0)),
                    "energy_month": float(detail.get("formulaMoney", 0)),  # à ajuster si autre champ
                    "energy_total": float(detail.get("eTotal", 0)),
                }
            )

            return Response({
                "plant": detail.get("plantName"),
                "total_energy": detail.get("eTotal"),
                "power": detail.get("nominalPower"),
                "co2": detail.get("co2"),
                "trees": detail.get("tree")
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class FetchGrowattProductionView(APIView):
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Username and password required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            api = Growatt()
            api.login(username, password)

            plants = api.get_plants()
            plant_id = plants[0]["id"]
            detail = api.get_plant(plant_id)

            data = {
                "plantName": detail.get("plantName"),
                "country": detail.get("country"),
                "city": detail.get("city"),
                "creationDate": detail.get("creatDate"),
                "nominalPower": f'{detail.get("nominalPower")} W',
                "energyTotal": f'{detail.get("eTotal")} kWh',
                "energyToday": f'{detail.get("etoday")} kWh',
                "energyMonth": f'{detail.get("emonth")} kWh',
                "energyYear": f'{detail.get("eyear")} kWh',
                "co2": f'{detail.get("co2")} kg',
                "tree": detail.get("tree"),
                "currency": detail.get("moneyUnitText")
            }

            return Response(data, status=200)

        except Exception as e:
            return Response({
                "error": str(e),
                "trace": traceback.format_exc()
            }, status=500)


# production/views.py
class StoreGrowattCredentialsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email et mot de passe requis"}, status=400)

        creds, created = GrowattCredential.objects.get_or_create(user=request.user)
        creds.email = email
        creds.set_password(password)
        creds.save()

        return Response({"message": "Identifiants sauvegardés avec succès."})


class SyncWithStoredCredentialsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            creds = GrowattCredential.objects.get(user=request.user)
        except GrowattCredential.DoesNotExist:
            return Response({"error": "Aucun identifiant enregistré."}, status=404)

        api = Growatt()
        if not creds.check_password(request.data.get("password", "")):
            return Response({"error": "Mot de passe API invalide."}, status=403)

        try:
            api.login(creds.email, request.data["password"])
            plant = api.get_plants()[0]
            detail = api.get_plant(plant["id"])

            return Response({
                "plant": detail.get("plantName"),
                "production": {
                    "today": detail.get("etoday"),
                    "month": detail.get("emonth"),
                    "year": detail.get("eyear"),
                    "total": detail.get("eTotal"),
                }
            })
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class ProductionEntryViewSet(viewsets.ModelViewSet):
    queryset = ProductionData.objects.all()
    serializer_class = ProductionDataSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]