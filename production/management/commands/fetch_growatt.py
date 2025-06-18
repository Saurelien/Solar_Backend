from django.core.management.base import BaseCommand
from growattServer import GrowattApi
from production.models import ProductionEntry
from django.contrib.auth.models import User
import getpass

class Command(BaseCommand):
    help = 'Récupère les données de production depuis Growatt'

    def handle(self, *args, **kwargs):
        email = input("Adresse email Growatt : ")
        password = getpass.getpass("Mot de passe : ")

        api = GrowattApi()
        login = api.login(email, password)
        user_id = login['userId']

        plants = api.plant_list(user_id)
        for i, plant in enumerate(plants['data']):
            print(f"{i+1}. {plant['plantName']} (ID: {plant['plantId']})")

        plant_index = int(input("Sélectionner une installation : ")) - 1
        plant_id = plants['data'][plant_index]['plantId']

        data = api.plant_detail(plant_id)

        # Récupération de l'utilisateur connecté
        username = input("Nom d'utilisateur local (Django) : ")
        try:
            django_user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("Utilisateur non trouvé. Veuillez d'abord créer un compte local."))
            return

        entry = ProductionEntry.objects.create(
            user = django_user,
            current_power = float(data['currPower']),
            energy_today = float(data['todayEnergy']),
            energy_total = float(data['totalEnergy'])
        )

        self.stdout.write(self.style.SUCCESS(f"Données enregistrées pour {django_user.username} : {entry}"))