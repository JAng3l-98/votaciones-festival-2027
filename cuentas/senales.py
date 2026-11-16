"""Mensajes al ingresar y al salir (entrega final)."""
from django.contrib import messages
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver


@receiver(user_logged_in, dispatch_uid="mensaje_al_ingresar")
def mensaje_al_ingresar(sender, request, user, **kwargs):
    if request is not None:
        nombre = user.first_name or user.email
        messages.success(request, f"Hola, {nombre}. Ingresaste correctamente.", fail_silently=True)


@receiver(user_logged_out, dispatch_uid="mensaje_al_salir")
def mensaje_al_salir(sender, request, user, **kwargs):
    if request is not None:
        messages.info(request, "Cerraste tu sesión.", fail_silently=True)
