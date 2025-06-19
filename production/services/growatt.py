from datetime import datetime, timedelta
from decouple import config
import requests
from production.models import GrowattCredential, WeatherCredential, ProductionData
import growattServer


def fetch_production_data_with_credentials(user):
    try:
        creds = GrowattCredential.objects.get(user=user)
    except GrowattCredential.DoesNotExist:
        return {"error": "Token Growatt manquant"}, 404

    if not creds.password_hash:
        return {"error": "Aucun token Growatt enregistré"}, 400

    try:
        raw_token = config("GROWATT_API_TOKEN")
    except:
        return {"error": "Token Growatt non trouvé en .env"}, 400

    if not creds.check_token(raw_token):
        return {"error": "Token invalide"}, 403

    try:
        api = growattServer.OpenApiV1(token=raw_token)
        plants = api.plant_list()
        if not plants.get("plants"):
            return {"error": "Aucune installation détectée"}, 404

        plant = plants["plants"][0]
        plant_id = plant["plant_id"]
        plant_name = plant.get("name", "Inconnu")
        plant_city = plant.get("city", "Inconnu")

        overview = api.plant_energy_overview(plant_id)
        device_sn = api.device_list(plant_id)["devices"][0]["device_sn"]
        min_energy = api.min_energy(device_sn)

        try:
            pac_value = float(min_energy.get("pac", 0))
        except (TypeError, ValueError):
            pac_value = 0.0
        current_power_kw = pac_value / 1000

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
        except:
            pass

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

    except Exception as e:
        return {"error": str(e)}, 500  # ✅ maintenant il y a un except !

    return {
        "plant": {
            "id": plant_id,
            "name": plant_name,
            "city": plant_city,
            "last_update": overview.get("last_update_time", "N/A"),
        },
        "production": {
            "today": today_energy,
            "month": overview.get("monthly_energy", "N/A"),
            "year": overview.get("yearly_energy", "N/A"),
            "total": overview.get("total_energy", "N/A"),
            "co2_saved": overview.get("carbon_offset", "N/A"),
            "efficiency": f"{efficiency} %" if efficiency is not None else "Non calculable",
            "power_now": current_power_kw,
            "cloud_cover": f"{cloud_percent} %" if cloud_percent is not None else "N/A",
        }
    }, 200


def get_production_aggregates(user):
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today.replace(day=1)
    year_ago = today.replace(month=1, day=1)

    def sum_field(queryset, field):
        return round(sum(getattr(e, field, 0) for e in queryset), 2)

    entries = ProductionData.objects.filter(user=user)
    data = {
        "daily": sum_field(entries.filter(date=today), "energy_today"),
        "weekly": sum_field(entries.filter(date__gte=week_ago), "energy_today"),
        "monthly": sum_field(entries.filter(date__gte=month_ago), "energy_today"),
        "yearly": sum_field(entries.filter(date__gte=year_ago), "energy_today"),
        "total": sum_field(entries, "energy_today"),
    }
    return data
