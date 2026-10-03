from django.urls import path

from .views import calculate_xg, health

urlpatterns = [
    path("health/", health, name="health"),
    path("xg/calculate/", calculate_xg, name="calculate_xg"),
]
