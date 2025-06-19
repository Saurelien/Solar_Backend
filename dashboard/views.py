from django.http import HttpResponse
from django.core.serializers.json import DjangoJSONEncoder
import json
import zipfile
import io
from django.utils.timezone import now
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from production.models import ProductionData


class ExportRawProductionData(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = now().date()

        entries = ProductionData.objects.filter(user=user).order_by('-date')
        if not entries.exists():
            return Response({"error": "Aucune donnée disponible"}, status=404)

        raw_data = []
        for entry in entries:
            raw_data.append({
                "date": entry.date.isoformat(),
                "plant_id": entry.plant_id,
                "power_now": entry.power_now,
                "energy_today": entry.energy_today,
                "energy_month": entry.energy_month,
                "energy_total": entry.energy_total
            })

        # Crée un fichier ZIP contenant un fichier JSON
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
            json_data = json.dumps(raw_data, cls=DjangoJSONEncoder, indent=2)
            z.writestr("production_data.json", json_data)
        buffer.seek(0)

        response = HttpResponse(buffer, content_type="application/zip")
        response['Content-Disposition'] = 'attachment; filename=production_export.zip'
        return response


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = now().date()
        start_month = today.replace(day=1)
        start_year = today.replace(month=1, day=1)

        queryset = ProductionData.objects.filter(user=user)

        def sum_field(queryset, field_name):
            return round(sum(getattr(entry, field_name, 0) or 0 for entry in queryset), 2)

        data_today = queryset.filter(date=today)
        data_month = queryset.filter(date__gte=start_month)
        data_year = queryset.filter(date__gte=start_year)
        data_all = queryset

        return Response({
            "summary": {
                "today_energy": sum_field(data_today, "energy_today"),
                "month_energy": sum_field(data_month, "energy_today"),
                "year_energy": sum_field(data_year, "energy_today"),
                "total_energy": sum_field(data_all, "energy_today"),
            },
            "last_entry": {
                "date": data_today.first().date if data_today.exists() else "N/A",
                "power_now": data_today.first().power_now if data_today.exists() else "N/A"
            }
        })