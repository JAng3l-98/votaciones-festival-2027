from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import IngresoForm

app_name = "cuentas"

urlpatterns = [
    path("ingresar/", auth_views.LoginView.as_view(authentication_form=IngresoForm), name="login"),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("registro/", views.registro, name="registro"),
]
