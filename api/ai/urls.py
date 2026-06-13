from django.urls import path

from .views import command_center_query, command_center_health

urlpatterns = [
    path("query", command_center_query),
    path("health", command_center_health),
]
