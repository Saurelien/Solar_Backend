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
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token

from accounts.views import RegisterView
from dashboard.views import ExportRawProductionData, DashboardSummaryView
from production.views import (GrowattV1OverviewView,
                              StoreGrowattTokenView, UseGrowattTokenView, SyncWithStoredCredentialsView,
                              StoreWeatherTokenView)

router = DefaultRouter()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-token-auth/', obtain_auth_token),
    path('api/accounts/register/', RegisterView.as_view(), name='register'),
    path('api/growatt/v1/overview/', GrowattV1OverviewView.as_view(), name='growatt-v1-overview'),
    path('api/growatt/token/store/', StoreGrowattTokenView.as_view(), name='store-growatt-token'),
    path('api/growatt/token/use/', UseGrowattTokenView.as_view(), name='use-growatt-token'),
    path('api/growatt/sync/', SyncWithStoredCredentialsView.as_view(), name='growatt-sync'),
    path('api/dashboard/export-raw/', ExportRawProductionData.as_view(), name='export-raw'),
    path('api/weather/token/store/', StoreWeatherTokenView.as_view(), name='store-weather-token'),
    path("summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui')
]

# Ajouter les routes DRF au fur et a mesure
urlpatterns += router.urls

