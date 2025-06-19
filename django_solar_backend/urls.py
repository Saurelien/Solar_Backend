"""
URL configuration for django_solar_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from accounts.views import RegisterView
from dashboard.views import DashboardOverviewView, export_data, import_data
from production.views import GrowattV1OverviewView, StoreGrowattTokenView, UseGrowattTokenView

router = DefaultRouter()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-token-auth/', obtain_auth_token),
    path('api/accounts/register/', RegisterView.as_view(), name='register'),
    path('api/dashboard/overview/', DashboardOverviewView.as_view(), name='dashboard-overview'),
    path('api/dashboard/export/', export_data, name='export_data'),
    path('api/dashboard/import/', import_data, name='import_data'),
    path('api/growatt/v1/overview/', GrowattV1OverviewView.as_view(), name='growatt-v1-overview'),
    path('api/growatt/token/store/', StoreGrowattTokenView.as_view(), name='store-growatt-token'),
    path('api/growatt/token/use/', UseGrowattTokenView.as_view(), name='use-growatt-token'),
]

# Ajouter les routes DRF au fur et a mesure
urlpatterns += router.urls

