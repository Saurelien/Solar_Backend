from django.db import models
from django.contrib.auth.models import User

class ProductionEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entries')
    timestamp = models.DateTimeField(auto_now_add=True)
    current_power = models.FloatField(help_text="Puissance actuelle en watts")
    energy_today = models.FloatField(help_text="Production journalière en kWh")
    energy_total = models.FloatField(help_text="Production totale en kWh")

    def __str__(self):
        return f"{self.timestamp} - {self.current_power} W"