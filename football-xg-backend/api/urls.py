from django.urls import path

from .views import ai_match_summary, calculate_xg, health

urlpatterns = [
    path("health/", health, name="health"),
    path("ai/match-summary/", ai_match_summary, name="ai_match_summary"),
    path("xg/calculate/", calculate_xg, name="calculate_xg"),
]
