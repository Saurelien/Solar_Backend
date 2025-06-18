from growattServer import GrowattApi

# Remplace par tes identifiants ShinePhone
EMAIL = "cstematik@gmail.com"
PASSWORD = "R1a2i3n4"

api = GrowattApi()


print("🔐 Connexion...")

api = GrowattApi()
api.server_url = "https://server.growatt.com/"  # <- C'est ça qui corrige tout

login_response = api.login(EMAIL, PASSWORD)
print(f"✅ Connecté : {login_response}")

print("🌿 Liste des installations :")
plants = api.plant_list(login_response['userId'])
for i, plant in enumerate(plants['data']):
    print(f"{i+1}. {plant['plantName']} (ID: {plant['plantId']})")

# Récupération des données pour le premier plant
plant_id = plants['data'][0]['plantId']
print(f"\n📊 Données pour l'installation '{plants['data'][0]['plantName']}' (ID: {plant_id})")
plant_data = api.plant_detail(plant_id)['data']

print(f" - Puissance actuelle : {plant_data['currPower']} W")
print(f" - Énergie aujourd'hui : {plant_data['todayEnergy']} kWh")
print(f" - Énergie totale : {plant_data['totalEnergy']} kWh")
