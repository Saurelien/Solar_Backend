import getpass
import hashlib
from django.core.management.base import BaseCommand
import growattServer
from rich.console import Console
from rich.table import Table

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
            # TODO DEBUG affiche la liste du plant service solaire
            print(f"PLANT active: {plant}")
            plant_id = plant['plant_id']
            plant_name = plant.get('name', 'Inconnu')
            plant_city = plant.get('city', 'Inconnu')
            print(f"[DEBUG] plant_id : {plant_id}")

            overview = api.plant_energy_overview(plant_id)
            print(f"[DEBUG] Résultat plant_energy_overview : {overview}")
            data = overview

            #TODO Table jour
            table_jour = Table(title="☀️ Production quotidienne", style="bright_yellow")
            table_jour.add_column("Date", style="cyan")
            table_jour.add_column("Énergie (kWh)", style="green")
            table_jour.add_row(data.get("last_update_time", "N/A"), data.get("today_energy", "N/A"))

            # TODO Table mois
            table_mois = Table(title="📅 Production mensuelle", style="bright_magenta")
            table_mois.add_column("Mois en cours", style="cyan")
            table_mois.add_column("Énergie (kWh)", style="green")
            table_mois.add_row(data.get("last_update_time", "N/A")[:7], data.get("monthly_energy", "N/A"))

            #TODO Table année
            table_annee = Table(title="📈 Production annuelle", style="bright_blue")
            table_annee.add_column("Année en cours", style="cyan")
            table_annee.add_column("Énergie (kWh)", style="green")
            table_annee.add_row(data.get("last_update_time", "N/A")[:4], data.get("yearly_energy", "N/A"))

            # TOTO Conversion fuseau horaire
            tz_raw = data.get("timezone", "N/A")
            tz_map = {
                "GMT+2": "France (UTC+2)",
                "GMT+1": "France (UTC+1)",
                "UTC": "UTC",
            }
            tz_human = tz_map.get(tz_raw, tz_raw)

            # Table total + détails
            table_total = Table(title="🔆 Production totale & Installation", style="bold green")
            table_total.add_column("Indicateur", style="cyan")
            table_total.add_column("Valeur", style="green")

            efficiency = data.get("efficiency")
            efficiency_str = f"{efficiency} %" if efficiency else "Non communiqué"

            details = {
                "Nom de l'installation": plant_name,
                "Localisation": plant_city,
                "Fuseau horaire": tz_human,
                "Production Totale (kWh)": data.get("total_energy", "N/A"),
                "CO₂ économisé (kg)": data.get("carbon_offset", "N/A"),
                "Dernière mise à jour": data.get("last_update_time", "N/A"),
                "Puissance actuelle (kW)": str(data.get("current_power", "N/A")),
                "Efficacité estimée": efficiency_str,
            }

            for k, v in details.items():
                table_total.add_row(k, v)

            # Affichage
            console.print(table_jour)
            console.print(table_mois)
            console.print(table_annee)
            console.print(table_total)

        except Exception as e:
            console.print(f"[bold red]Erreur : {e}[/bold red]")
