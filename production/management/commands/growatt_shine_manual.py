# from django.core.management.base import BaseCommand
# from growatt import Growatt
# from rich.console import Console
# from rich.table import Table
# from datetime import date
# import getpass
#
# class Command(BaseCommand):
#     help = "Connexion à l'API Growatt (email+mot de passe) et affichage des productions"
#
#     def handle(self, *args, **kwargs):
#         console = Console()
#
#         email = input("Adresse email ShinePhone : ").strip()
#         password = getpass.getpass("Mot de passe ShinePhone : ")
#
#         try:
#             api = Growatt()
#             api.login(email, password)
#
#             plants = api.get_plants()
#             if not plants:
#                 raise Exception("Aucune installation trouvée pour cet utilisateur.")
#             plant = plants[0]
#             plant_id = plant["id"]
#
#             console.print("\n[bold cyan]🌱 Infos Installation[/bold cyan]")
#             table = Table(show_header=True, header_style="bold blue")
#             table.add_column("Champ")
#             table.add_column("Valeur")
#             for key, value in plant.items():
#                 table.add_row(str(key), str(value))
#             console.print(table)
#
#             # 🔍 Récupération des devices pour obtenir le SN et le type
#             devices_response = api.session.post(
#                 f"{api.BASE_URL}/panel/getDevicesByPlant?plantId={plant_id}"
#             )
#             devices_response.raise_for_status()
#             device_info = devices_response.json().get("obj", {})
#
#             sn = None
#             device_type = None
#             for key, devices in device_info.items():
#                 if isinstance(devices, list) and len(devices) > 0:
#                     sn = devices[0][0]
#                     device_type = key
#                     console.print(f"[bold yellow]Type détecté : {device_type} — SN : {sn}[/bold yellow]")
#                     break
#
#             if not sn:
#                 raise Exception("Aucun onduleur détecté dans les devices.")
#
#             # 📆 Dates
#             today = date.today()
#             today_str = today.strftime("%Y-%m-%d")
#             month_str = today.strftime("%Y-%m")
#             year_str = today.strftime("%Y")
#
#             # 📊 Production journalière, mensuelle, annuelle
#             daily = api.get_energy_stats_daily(today_str, plant_id, sn).get("obj", {})
#             monthly = api.get_energy_stats_monthly(month_str, plant_id, sn).get("obj", {})
#             yearly = api.get_energy_stats_yearly(year_str, plant_id, sn).get("obj", {})
#
#             # 🔁 Total selon le type
#             if device_type == "mix":
#                 total = api.get_mix_total(plant_id, sn)
#             elif device_type == "tlx":
#                 total = api.get_tlx_status(plant_id, sn)  # ← remplacé ici
#             else:
#                 total = {}
#
#             # Fonction d'affichage
#             def afficher_tableau(titre, données):
#                 table = Table(title=titre, show_header=True, header_style="bold magenta")
#                 table.add_column("Clé", style="cyan", no_wrap=True)
#                 table.add_column("Valeur", style="green")
#                 for k, v in données.items():
#                     if isinstance(v, list):
#                         continue
#                     table.add_row(str(k), str(v))
#                 console.print(table)
#
#             afficher_tableau("🌞 Production Aujourd'hui", daily)
#             afficher_tableau("📆 Production du Mois", monthly)
#             afficher_tableau("📈 Production de l'Année", yearly)
#             afficher_tableau("🔁 Production Totale", total)
#
#         except Exception as e:
#             console.print(f"[bold red]Erreur : {e}[/bold red]")

# from django.core.management.base import BaseCommand
# from growattServer import GrowattApi
# from rich.console import Console
# from rich.table import Table
# from datetime import date
# import getpass
#
#
# class Command(BaseCommand):
#     help = "Connexion à l'API Growatt (token OU email+mot de passe) et affichage des productions"
#
#     def handle(self, *args, **kwargs):
#         console = Console()
#         console.print("[bold cyan]Connexion à l'API Growatt[/bold cyan]")
#
#         use_token = input("Souhaitez-vous utiliser un token API ? (o/n) : ").strip().lower() == "o"
#
#         try:
#             api = GrowattApi()
#             sn = None
#             plant_id = None
#             today = date.today()
#             today_str = today.strftime("%Y-%m-%d")
#
#             if use_token:
#                 token = input("Token API Growatt : ").strip()
#                 console.print("[yellow]Connexion par token définie (⚠️ certaines méthodes peuvent être limitées).[/yellow]")
#                 raise NotImplementedError("L'API token n'est pas encore intégrée via cette lib. Utilise login utilisateur pour l’instant.")
#
#             else:
#                 email = input("Adresse email ShinePhone : ").strip()
#                 password = getpass.getpass("Mot de passe ShinePhone : ")
#                 login_data = api.login(email, password)
#
#                 if not login_data["success"]:
#                     raise Exception(f"Échec de connexion : {login_data.get('msg', 'inconnu')}")
#
#                 # Récupération de l'onduleur
#                 inverters = api.plant_list()
#                 if not inverters:
#                     raise Exception("Aucune installation détectée.")
#
#                 first = inverters[0]
#                 sn = first["deviceSn"]
#                 plant_id = first["plantId"]
#
#                 console.print(f"[green]Onduleur détecté : {sn} (Plant ID : {plant_id})[/green]")
#
#                 # Données de production
#                 status = api.get_tlx_status(plant_id, sn)
#                 energy = api.get_tlx_energy_overview(plant_id, sn)
#                 chart = api.inverter_detail(plant_id, sn)
#
#                 def afficher_tableau(titre, données):
#                     table = Table(title=titre, show_header=True, header_style="bold magenta")
#                     table.add_column("Clé", style="cyan", no_wrap=True)
#                     table.add_column("Valeur", style="green")
#                     for k, v in données.items():
#                         if isinstance(v, list):
#                             continue
#                         table.add_row(str(k), str(v))
#                     console.print(table)
#
#                 afficher_tableau("⚡ État général de l'onduleur", status.get("data", {}))
#                 afficher_tableau("🔁 Vue d'ensemble de la production", energy.get("data", {}))
#                 afficher_tableau("📊 Données détaillées", chart.get("data", {}))
#
#         except Exception as e:
#             console.print(f"[bold red]Erreur : {e}[/bold red]")
#

from django.core.management.base import BaseCommand
from rich.console import Console
from rich.table import Table
from datetime import date
import requests
import getpass

class Command(BaseCommand):
    help = "Connexion à l'API Growatt V1 (token) et affichage des données de production"

    def handle(self, *args, **kwargs):
        console = Console()
        console.print("[bold]Connexion à l'API Growatt OpenAPI V1 (token requis)[/bold]")
        token = input("Token API Growatt : ").strip()

        headers = {
            "Content-Type": "application/json",
            "token": token,
        }

        try:
            # 🔍 Récupération des installations
            plant_url = "https://openapi.growatt.com/plant/getPlantList"
            plant_resp = requests.post(plant_url, headers=headers, json={})
            plant_resp.raise_for_status()
            plant_data = plant_resp.json()
            plant = plant_data["data"]["plants"][0]
            plant_id = plant["plantId"]
            plant_name = plant["plantName"]

            console.print(f"\n[bold cyan]🌱 Installation détectée : {plant_name}[/bold cyan]")
            info_table = Table(show_header=True, header_style="bold blue")
            info_table.add_column("Champ")
            info_table.add_column("Valeur")
            info_table.add_row("ID", str(plant_id))
            info_table.add_row("Nom", plant_name)
            console.print(info_table)

            # 🔧 Récupération des onduleurs
            inv_url = "https://openapi.growatt.com/device/getDevices"
            inv_resp = requests.post(inv_url, headers=headers, json={"plantId": plant_id})
            inv_resp.raise_for_status()
            inverter = inv_resp.json()["data"]["devices"][0]
            sn = inverter["deviceSn"]

            console.print(f"\n[bold yellow]Onduleur détecté : {sn}[/bold yellow]")

            # 📅 Dates
            today = date.today()
            today_str = today.strftime("%Y-%m-%d")

            # 📊 Données journalières
            day_url = "https://openapi.growatt.com/newInverterDataService/getInverterEnergyDayChart"
            day_resp = requests.post(day_url, headers=headers, json={
                "deviceSn": sn,
                "date": today_str
            })
            day_resp.raise_for_status()
            day_data = day_resp.json()["data"]

            table = Table(title=f"🌞 Production de la journée ({today_str})", header_style="bold magenta")
            table.add_column("Heure")
            table.add_column("Énergie (kWh)")

            for t, v in zip(day_data["x"], day_data["y"]):
                table.add_row(t, str(v))

            console.print(table)

        except Exception as e:
            console.print(f"[bold red]Erreur : {e}[/bold red]")