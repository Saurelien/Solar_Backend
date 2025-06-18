from growatt import Growatt
from rich.console import Console
from rich.table import Table

# Initialisation de la console rich
console = Console()

# Connexion à l'API Growatt
api = Growatt()
api.login("cstematik@gmail.com", "R1a2i3n4")

# Récupération des installations
plants = api.get_plants()
plant_id = plants[0]["id"]

# Détails de l’installation
detail = api.get_plant(plant_id)

# Création d’un tableau
table = Table(title="📊 Détail de la production Growatt", show_header=True, header_style="bold magenta")
table.add_column("Clé", style="cyan", no_wrap=True)
table.add_column("Valeur", style="green")

# Ajout des champs principaux au tableau
fields_to_display = [
    ("Nom de l'installation", detail.get("plantName")),
    ("Pays", detail.get("country")),
    ("Ville", detail.get("city")),
    ("Date création", detail.get("creatDate")),
    ("Puissance nominale", f'{detail.get("nominalPower")} W'),
    ("Énergie totale", f'{detail.get("eTotal")} kWh'),
    ("Équivalent CO₂ évité", f'{detail.get("co2")} kg'),
    ("Arbres sauvés", f'{detail.get("tree")}'),
    ("Unité monétaire", detail.get("moneyUnitText")),
]

for key, value in fields_to_display:
    table.add_row(key, str(value))

# Affichage du tableau
console.print(table)
