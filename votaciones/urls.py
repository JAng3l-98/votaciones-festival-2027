from django.urls import path

from . import views

app_name = "votaciones"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("categorias/", views.categorias, name="categorias"),
    path("votaciones/", views.lista, name="lista"),
    path("votaciones/<int:pk>/", views.detalle, name="detalle"),
]
