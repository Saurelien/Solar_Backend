import getpass
import hashlib
from django.core.management.base import BaseCommand
import growattServer
from rich.console import Console
from rich.table import Table
from rich import box
from datetime import datetime
from decouple import RepositoryEnv, Config
import requests
import os

# Charge manuellement un fichier .env spécifique
env_path = os.path.join(os.path.dirname(__file__), '../../../.venv/secret.env')
config = Config(RepositoryEnv(env_path))

OPENWEATHER_API_KEY = config('OPENWEATHER_API_KEY')

class Command(BaseCommand):
    help = "Affiche les productions solaire jour/mois/année/total via l'API Growatt"

    def handle(self, *args, **kwargs):
        console = Console()
        console.print("🔌 Connexion à l'API Growatt ShinePhone (V1)", style="bold cyan")

        token = getpass.getpass("Token API Growatt (non visible) : ").strip()
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        print(f"[DEBUG] Token saisi (hash) : {token_hash}")

        try:
            api = growattServer.OpenApiV1(token=token)
            print("[DEBUG] API initialisée avec succès.")

            plants = api.plant_list()
            print(f"[DEBUG] Résultat plant_list : {plants}")

            if 'plants' not in plants or not plants['plants']:
                raise Exception("Aucune installation détectée.")

            plant = plants['plants'][0]
            print(f"PLANT active: {plant}")
            plant_id = plant['plant_id']
            plant_name = plant.get('name', 'Inconnu')
            plant_city = plant.get('city', 'Inconnu')
            print(f"[DEBUG] plant_id : {plant_id}")

            # 📡 API Météo - couverture nuageuse à l'emplacement du site
            cloud_percent = None
            try:
                weather_url = (
                    f"http://api.openweathermap.org/data/2.5/weather?"
                    f"q={plant_city}&appid={OPENWEATHER_API_KEY}&units=metric&lang=fr"
                )
                response = requests.get(weather_url, timeout=10)
                response.raise_for_status()
                weather_data = response.json()
                cloud_percent = weather_data.get("clouds", {}).get("all", 0)
                print(f"[DEBUG] Couverture nuageuse à {plant_city} : {cloud_percent} %")
            except Exception as e:
                print(f"[DEBUG] Erreur récupération météo : {e}")

            overview = api.plant_energy_overview(plant_id)
            print(f"[DEBUG] Résultat plant_energy_overview : {overview}")
            # 🔍 Récupération du numéro de série de l'onduleur
            devices = api.device_list(plant_id)
            print(f"[DEBUG] device_list : {devices}")

            if not devices.get("devices"):
                raise Exception("Aucun onduleur trouvé pour cette installation.")

            device_sn = devices["devices"][0]["device_sn"]
            print(f"[DEBUG] Numéro de série de l'onduleur : {device_sn}")

            # 🔋 Récupération de la puissance actuelle depuis l'onduleur
            min_energy = api.min_energy(device_sn)
            print(f"[DEBUG] Données min_energy : {min_energy}")

            try:
                pac_value = min_energy.get("pac", 0)
                current_power_kw = float(pac_value) / 1000
            except Exception as e:
                print(f"[DEBUG] Erreur puissance actuelle : {e}")
                current_power_kw = 0

            current_power = min_energy.get("power", "N/A")  # en watts
            current_power_kw = float(current_power) / 1000 if current_power != "N/A" else 0
            data = overview

            #TODO Table jour
            table_jour = Table(title="☀️ Production quotidienne",
                               style="bright_yellow",
                               box=box.ROUNDED)
            table_jour.add_column("Date", style="cyan")
            table_jour.add_column("Énergie (kWh)", style="green")
            table_jour.add_row(data.get("last_update_time", "N/A"), data.get("today_energy", "N/A"))

            # TODO Table mois
            table_mois = Table(title="📅 Production mensuelle",
                               style="bright_magenta",
                               box=box.ROUNDED)
            table_mois.add_column("Mois en cours", style="cyan")
            table_mois.add_column("Énergie (kWh)", style="green")
            table_mois.add_row(data.get("last_update_time", "N/A")[:7], data.get("monthly_energy", "N/A"))

            #TODO Table année
            table_annee = Table(title="📈 Production annuelle",
                                style="bright_blue",
                                box=box.ROUNDED)
            table_annee.add_column("Année en cours", style="cyan")
            table_annee.add_column("Énergie (kWh)", style="green")
            table_annee.add_row(data.get("last_update_time", "N/A")[:4], data.get("yearly_energy", "N/A"))

            # ✅ Tableau à 3 colonnes : Emoji | Indicateur | Valeur
            table_global = Table(
                title="📋 Détails globaux de l'installation",
                title_justify="center",
                title_style="bold yellow",
                caption="Généré avec Rich",
                caption_style="dim",
                box=box.SIMPLE,
                expand=True,
                show_lines=True,
                row_styles=["none", "dim"]
            )

            # Colonnes
            table_global.add_column("Indicateur", header_style="bright_yellow", style="cyan", justify="center")
            table_global.add_column("Valeur", header_style="bright_yellow", style="green", justify="center")

            # Fuseau horaire lisible
            tz_raw = data.get("timezone", "N/A")
            tz_map = {
                "GMT+2": "France (UTC+2)",
                "GMT+1": "France (UTC+1)",
                "UTC": "Temps universel (UTC)",
            }
            tz_human = tz_map.get(tz_raw, tz_raw)

            NOMINAL_POWER_KW = 0.8  # 800W = 0.8 kW

            # Production réelle ajustée à la couverture nuageuse
            try:
                today_energy = float(data.get("today_energy", 0))  # en kWh
                now = datetime.now()
                hours_passed = now.hour + now.minute / 60
                theoretical_production = NOMINAL_POWER_KW * hours_passed

                if theoretical_production > 0:
                    if cloud_percent is not None:
                        adjusted_theoretical = theoretical_production * ((100 - cloud_percent) / 100)
                        adjusted_efficiency = (today_energy / adjusted_theoretical) * 100
                        efficiency_str = f"{adjusted_efficiency:.2f} % (ajustée météo)"
                    else:
                        raw_efficiency = (today_energy / theoretical_production) * 100
                        efficiency_str = f"{raw_efficiency:.2f} %"
                else:
                    efficiency_str = "Non calculable"
            except Exception as e:
                print(f"[DEBUG] Erreur calcul efficacité : {e}")
                efficiency_str = "Non communiqué"


            # Champs à afficher
            global_details = [
                ("Nom de l'installation", plant_name),
                ("Localisation", plant_city),
                ("Fuseau horaire", tz_human),
                ("Couverture nuageuse", f"{cloud_percent} %" if cloud_percent is not None else "N/A"),
                ("Production aujourd'hui (kWh)", data.get("today_energy", "N/A")),
                ("Production ce mois-ci (kWh)", data.get("monthly_energy", "N/A")),
                ("Production cette année (kWh)", data.get("yearly_energy", "N/A")),
                ("Production totale (kWh)", data.get("total_energy", "N/A")),
                ("CO₂ économisé (kg)", data.get("carbon_offset", "N/A")),
                ("Puissance actuelle", f"{int(pac_value)} W ({current_power_kw:.2f} kW)"),
                ("Efficacité estimée", efficiency_str),
                ("Dernière mise à jour", data.get("last_update_time", "N/A")),
            ]

            # Remplissage
            for label, value in global_details:
                table_global.add_row(label, str(value))

            # Affichage des tableaux
            console.print(table_jour)
            console.print(table_mois)
            console.print(table_annee)
            console.print(table_global)

        except Exception as e:
            console.print(f"[bold red]Erreur : {e}[/bold red]")
