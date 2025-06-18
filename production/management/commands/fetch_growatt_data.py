import requests
from django.core.management.base import BaseCommand
from production.models import ProductionData
from growattServer import GrowattApi


API_TOKEN = "h2mi6no01yegj6px93qnj7h1z9o7t20w"
BASE_URL = "https://server-api.growatt.com"
HEADERS = {
    "Content-Type": "application/json",
    "token": API_TOKEN,
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
}

def get_plant_detail():
    plant_id = "BZP6P1D08G"
    url = f"{BASE_URL}/plant/getPlantData"
    payload = {"plantId": plant_id}
    response = requests.post(url, headers=HEADERS, json=payload)
    response.raise_for_status()
    return response.json()

class Command(BaseCommand):
    help = "Récupère la production via Growatt login"

    def handle(self, *args, **kwargs):
        api = GrowattApi()

        email = "cstematik@gmail.com"
        password = "R1a2i3n4567567887"

        try:
            login_response = api.login(email, password)
            user_id = login_response['userId']
            plants = api.plant_list(user_id)
            plant_id = plants['data'][0]['plantId']
            detail = api.plant_detail(plant_id)['data']

            ProductionData.objects.create(
                current_power=detail.get("currPower"),
                today_energy=detail.get("todayEnergy"),
                month_energy=detail.get("monthEnergy"),
                total_energy=detail.get("totalEnergy"),
            )
            self.stdout.write(self.style.SUCCESS("✅ Données enregistrées avec succès."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"❌ Erreur Growatt API: {e}"))
