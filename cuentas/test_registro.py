"""Pruebas del registro de usuarios.  Ejecutar: python manage.py test cuentas"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

Usuario = get_user_model()

DATOS_VALIDOS = {
    "first_name": "Ana",
    "last_name": "Pérez",
    "email": "ana@correo.com",
    "password1": "Acordeon-Valle-2027",
    "password2": "Acordeon-Valle-2027",
    "acepta_tratamiento_datos": "on",
}


class RegistroTests(TestCase):
    def test_la_pagina_de_registro_responde(self):
        respuesta = self.client.get(reverse("cuentas:registro"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Crea tu cuenta")

    def test_registro_valido_crea_el_usuario_con_la_autorizacion(self):
        respuesta = self.client.post(reverse("cuentas:registro"), DATOS_VALIDOS)
        self.assertRedirects(respuesta, reverse("cuentas:login"))
        usuario = Usuario.objects.get(email="ana@correo.com")
        self.assertTrue(usuario.acepta_tratamiento_datos)
        self.assertIsNotNone(usuario.fecha_aceptacion_datos)
        self.assertTrue(usuario.check_password("Acordeon-Valle-2027"))

    def test_no_se_registra_un_correo_repetido(self):
        self.client.post(reverse("cuentas:registro"), DATOS_VALIDOS)
        repetido = dict(DATOS_VALIDOS, email="ANA@correo.com", first_name="Otra")
        respuesta = self.client.post(reverse("cuentas:registro"), repetido)
        self.assertContains(respuesta, "Ya existe una cuenta con este correo")
        self.assertEqual(Usuario.objects.count(), 1)

    def test_sin_autorizacion_de_datos_no_se_crea_la_cuenta(self):
        sin_autorizacion = dict(DATOS_VALIDOS)
        del sin_autorizacion["acepta_tratamiento_datos"]
        respuesta = self.client.post(reverse("cuentas:registro"), sin_autorizacion)
        self.assertContains(respuesta, "Debes autorizar el tratamiento de tus datos")
        self.assertFalse(Usuario.objects.exists())

    def test_contrasenas_distintas_no_se_aceptan(self):
        distintas = dict(DATOS_VALIDOS, password2="Otra-Clave-2027")
        self.client.post(reverse("cuentas:registro"), distintas)
        self.assertFalse(Usuario.objects.exists())
