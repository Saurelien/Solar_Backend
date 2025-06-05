from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from production.models import ProductionEntry
from django.utils.timezone import now

class DashboardOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        today = now().date()

        entries_today = ProductionEntry.objects.filter(user=user, timestamp__date=today)

        total_today_kWh = sum(e.energy_today for e in entries_today)
        current_power = entries_today.last().current_power if entries_today.exists() else 0
        count_entries = entries_today.count()

        return Response({
            "today_total_kWh": round(total_today_kWh, 2),
            "current_power_W": current_power,
            "entries_count_today": count_entries
        })