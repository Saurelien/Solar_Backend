from django.utils.timezone import now
from django.core.exceptions import ObjectDoesNotExist
from decouple import config
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import requests
from .models import GrowattCredential, ProductionData, WeatherCredential
import growattServer

from .services.growatt import fetch_production_data_with_credentials, get_production_aggregates


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


class SyncWithStoredCredentialsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # 🔐 Récupération du token Growatt
        try:
            creds = GrowattCredential.objects.get(user=user)
        except GrowattCredential.DoesNotExist:
            return Response({"error": "Token Growatt manquant"}, status=404)

        if not creds.password_hash:
            return Response({"error": "Aucun token Growatt enregistré"}, status=400)

        try:
            raw_token = request.data.get("token") or config("GROWATT_API_TOKEN")
        except:
            return Response({"error": "Aucun token fourni ni trouvé en .env"}, status=400)

        if not creds.check_token(raw_token):
            return Response({"error": "Token invalide"}, status=403)

        try:
            # ⚡ Connexion API Growatt
            api = growattServer.OpenApiV1(token=raw_token)
            plants = api.plant_list()
            if not plants.get("plants"):
                return Response({"error": "Aucune installation détectée"}, status=404)

            plant = plants['plants'][0]
            plant_id = plant['plant_id']
            plant_name = plant.get('name', 'Inconnu')
            plant_city = plant.get('city', 'Inconnu')

            overview = api.plant_energy_overview(plant_id)
            device_sn = api.device_list(plant_id)["devices"][0]["device_sn"]
            min_energy = api.min_energy(device_sn)

            try:
                pac_value = float(min_energy.get("pac", 0))
            except (TypeError, ValueError):
                pac_value = 0.0
            current_power_kw = pac_value / 1000

            # ☁️ Récupération météo (clé perso ou .env)
            try:
                weather_creds = WeatherCredential.objects.get(user=user)
                weather_key = weather_creds.api_key
            except WeatherCredential.DoesNotExist:
                weather_key = config("OPENWEATHER_API_KEY")

            cloud_percent = None
            try:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={plant_city}&appid={weather_key}&units=metric&lang=fr"
                res = requests.get(url, timeout=10).json()
                cloud_percent = res.get("clouds", {}).get("all", 0)
            except Exception as e:
                print(f"[DEBUG] Météo non récupérée : {e}")

            # 📊 Calcul efficacité
            now = datetime.now()
            hours_passed = now.hour + now.minute / 60
            today_energy = float(overview.get("today_energy", 0))
            nominal_kw = 0.8
            theoretical = nominal_kw * hours_passed
            if theoretical > 0:
                if cloud_percent is not None:
                    adjusted = theoretical * ((100 - cloud_percent) / 100)
                    efficiency = round((today_energy / adjusted) * 100, 2)
                else:
                    efficiency = round((today_energy / theoretical) * 100, 2)
            else:
                efficiency = None

            # 💾 Enregistrement des données
            ProductionData.objects.update_or_create(
                user=user,
                plant_id=plant_id,
                date=now.date(),
                defaults={
                    "power_now": pac_value,
                    "energy_today": today_energy,
                    "energy_month": float(overview.get("monthly_energy", 0)),
                    "energy_total": float(overview.get("total_energy", 0)),
                }
            )

            return Response({
                "plant": {
                    "id": plant_id,
                    "name": plant_name,
                    "city": plant_city
                },
                "production": {
                    "today_energy": today_energy,
                    "efficiency": f"{efficiency} %" if efficiency is not None else "Non calculable",
                    "power_now_kw": current_power_kw,
                    "cloud_cover": f"{cloud_percent} %" if cloud_percent is not None else "N/A"
                }
            })

        except Exception as e:
            return Response({"error": str(e)}, status=500)


class StoreWeatherTokenView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw_key = request.data.get("token")
        if not raw_key:
            return Response({"error": "Clé API météo requise"}, status=400)

        creds, _ = WeatherCredential.objects.get_or_create(user=request.user)
        creds.api_key = raw_key
        creds.save()
        return Response({"message": "Clé météo enregistrée."})


class ProductionDayView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = get_production_aggregates(request.user)
        return Response({"daily": data["daily"]})


class ProductionWeekView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = get_production_aggregates(request.user)
        return Response({"weekly": data["weekly"]})


class ProductionMonthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = get_production_aggregates(request.user)
        return Response({"monthly": data["monthly"]})


class ProductionYearView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = get_production_aggregates(request.user)
        return Response({"yearly": data["yearly"]})


class ProductionTotalView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = get_production_aggregates(request.user)
        return Response({"total": data["total"]})


class InstallationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        result, status = fetch_production_data_with_credentials(request.user)
        return Response(result, status=status)