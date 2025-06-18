from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from production.models import ProductionData
from django.utils.timezone import now
from django.http import HttpResponse
from django.core import serializers
import zipfile
import io
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
import json

class DashboardOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = now().date()

        entries_today = ProductionData.objects.filter(user=user, timestamp__date=today)

        total_today_kWh = sum(e.energy_today for e in entries_today)
        current_power = entries_today.last().current_power if entries_today.exists() else 0
        count_entries = entries_today.count()

        return Response({
            "today_total_kWh": round(total_today_kWh, 2),
            "current_power_W": current_power,
            "entries_count_today": count_entries
        })

def export_data(request):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        for model in ['production.production', 'auth.user']:
            data = serializers.serialize('json', globals()['apps'].get_model(model).objects.all())
            z.writestr(f"{model}.json", data)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=solar_backup.zip'
    return response

@csrf_exempt
def import_data(request):
    if request.method == "POST" and request.FILES.get('zipfile'):
        zip_file = request.FILES['zipfile']
        with zipfile.ZipFile(zip_file) as z:
            for file in z.namelist():
                raw = z.read(file).decode()
                data = json.loads(raw)
                for obj in serializers.deserialize("json", json.dumps(data)):
                    obj.save()
        return HttpResponse("Données importées avec succès.")
    return HttpResponse("Fichier manquant ou méthode incorrecte.", status=400)