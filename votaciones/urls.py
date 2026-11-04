from django.urls import path

from . import api, views

app_name = "votaciones"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("categorias/", views.categorias, name="categorias"),
    path("votaciones/", views.lista, name="lista"),
    path("votaciones/<int:pk>/", views.detalle, name="detalle"),
    # Entrega 3: proceso de votación (solo POST) y comprobante
    path("votaciones/<int:pk>/confirmar/", views.confirmar, name="confirmar"),
    path("votaciones/<int:pk>/votar/", views.votar, name="votar"),
    path("votos/<str:comprobante>/", views.voto_registrado, name="voto_registrado"),
    # Entrega 3: API GET con las categorías y opciones en JSON
    path("api/categorias/", api.categorias, name="api_categorias"),
]
