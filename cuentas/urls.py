from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import CambiarContrasenaForm, IngresoForm, NuevaContrasenaForm, RecuperarContrasenaForm

app_name = "cuentas"

urlpatterns = [
    path("ingresar/", auth_views.LoginView.as_view(authentication_form=IngresoForm, redirect_authenticated_user=True),
         name="login"),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("registro/", views.registro, name="registro"),
    path("mis-votos/", views.mis_votos, name="mis_votos"),

    # Entrega final: recuperar la contraseña por correo (vistas de Django con las plantillas del sitio)
    path("contrasena/olvide/", auth_views.PasswordResetView.as_view(
        form_class=RecuperarContrasenaForm,
        template_name="cuentas/contrasena_olvide.html",
        email_template_name="cuentas/correo_restablecer.txt",
        subject_template_name="cuentas/correo_restablecer_asunto.txt",
        success_url=reverse_lazy("cuentas:password_reset_done"),
    ), name="password_reset"),
    path("contrasena/olvide/enviado/", auth_views.PasswordResetDoneView.as_view(
        template_name="cuentas/contrasena_enviado.html",
    ), name="password_reset_done"),
    path("contrasena/restablecer/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        form_class=NuevaContrasenaForm,
        template_name="cuentas/contrasena_restablecer.html",
        success_url=reverse_lazy("cuentas:password_reset_complete"),
    ), name="password_reset_confirm"),
    path("contrasena/restablecida/", auth_views.PasswordResetCompleteView.as_view(
        template_name="cuentas/contrasena_restablecida.html",
    ), name="password_reset_complete"),

    # Cambiar la contraseña con la sesión iniciada
    path("contrasena/cambiar/", auth_views.PasswordChangeView.as_view(
        form_class=CambiarContrasenaForm,
        template_name="cuentas/contrasena_cambiar.html",
        success_url=reverse_lazy("cuentas:password_change_done"),
    ), name="password_change"),
    path("contrasena/cambiada/", auth_views.PasswordChangeDoneView.as_view(
        template_name="cuentas/contrasena_cambiada.html",
    ), name="password_change_done"),
]
