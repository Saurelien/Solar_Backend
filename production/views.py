from .models import GrowattCredential, ProductionData
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import growattServer
from django.core.exceptions import ObjectDoesNotExist

class GrowattV1OverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw_token = request.data.get("token")
        if not raw_token:
            return Response({"error": "Token requis"}, status=400)

        try:
            creds = GrowattCredential.objects.get(user=request.user)
        except GrowattCredential.DoesNotExist:
            return Response({"error": "Aucun token enregistré"}, status=404)

        if not creds.check_token(raw_token):
            return Response({"error": "Token invalide"}, status=403)

        # ✔️ Token validé → démarrer appel Growatt
        try:
            api = growattServer.OpenApiV1(token=raw_token)
            plants = api.plant_list()

            if 'plants' not in plants or not plants['plants']:
                return Response({"error": "Aucune installation détectée"}, status=404)

            plant = plants['plants'][0]
            plant_id = plant['plant_id']
            plant_name = plant.get('name', 'Inconnu')
            plant_city = plant.get('city', 'Inconnu')

            data = api.plant_energy_overview(plant_id)

            tz_map = {
                "GMT+2": "France (UTC+2)",
                "GMT+1": "France (UTC+1)",
                "UTC": "UTC",
            }
            tz_human = tz_map.get(data.get("timezone", ""), data.get("timezone", "Inconnu"))
            efficiency = data.get("efficiency")
            efficiency_str = f"{efficiency} %" if efficiency else "Non communiqué"

            ProductionData.objects.update_or_create(
                user=request.user,
                plant_id=plant_id,
                date=now().date(),
                defaults={
                    "power_now": float(data.get("current_power", 0)),
                    "energy_today": float(data.get("today_energy", 0)),
                    "energy_month": float(data.get("monthly_energy", 0)),
                    "energy_total": float(data.get("total_energy", 0)),
                }
            )

            return Response({
                "plant": {
                    "id": plant_id,
                    "name": plant_name,
                    "city": plant_city,
                    "timezone": tz_human,
                    "last_update": data.get("last_update_time", "N/A"),
                },
                "production": {
                    "today": data.get("today_energy", "N/A"),
                    "month": data.get("monthly_energy", "N/A"),
                    "year": data.get("yearly_energy", "N/A"),
                    "total": data.get("total_energy", "N/A"),
                    "co2_saved": data.get("carbon_offset", "N/A"),
                    "efficiency": efficiency_str,
                    "power_now": data.get("current_power", "N/A"),
                }
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)
# production/views.py

# ✅ Vue pour enregistrer un token hashé
class StoreGrowattTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw_token = request.data.get("token")
        if not raw_token:
            return Response({"error": "Token requis"}, status=400)

        creds, _ = GrowattCredential.objects.get_or_create(user=request.user)
        creds.set_token(raw_token)
        creds.save()

        return Response({"message": "Token enregistré avec succès (hashé avec Argon2)."})


# ✅ Vue pour utiliser un token hashé
class UseGrowattTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw_token = request.data.get("token")
        if not raw_token:
            return Response({"error": "Token manquant"}, status=400)

        try:
            creds = GrowattCredential.objects.get(user=request.user)
        except ObjectDoesNotExist:
            return Response({"error": "Aucun token enregistré"}, status=404)

        if not creds.check_token(raw_token):
            return Response({"error": "Token invalide"}, status=403)

        # ✔️ Si le token est correct → récupération Growatt
        try:
            api = growattServer.OpenApiV1(token=raw_token)
            plants = api.plant_list()
            return Response({"plants": plants})
        except Exception as e:
            return Response({"error": str(e)}, status=500)
