from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone

class ProductionData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plant_id = models.CharField(max_length=100)
    date = models.DateField(auto_now_add=True)
    power_now = models.FloatField()
    energy_today = models.FloatField()
    energy_month = models.FloatField()
    energy_total = models.FloatField()


# production/models.py

class GrowattCredential(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField()
    password_hash = models.CharField(max_length=255)

    def set_token(self, raw_token):
        self.password_hash = make_password(raw_token, hasher='argon2')

    def check_token(self, raw_token):
        return check_password(raw_token, self.password_hash)

    def __str__(self):
        return f"Growatt API Credentials for {self.user.username}"
