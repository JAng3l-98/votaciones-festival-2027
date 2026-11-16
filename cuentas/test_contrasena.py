"""
Pruebas de recuperar y cambiar la contraseña, y de las páginas de error (entrega final).
Ejecutar: python manage.py test cuentas.test_contrasena -v 2
"""
import re

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

Usuario = get_user_model()
CLAVE = "Acordeon-Valle-2027"
NUEVA = "Guacharaca-Caja-2028"


class RecuperarContrasenaTests(TestCase):
    def setUp(self):
        self.ana = Usuario.objects.create_user(username="ana@correo.com", email="ana@correo.com",
                                               password=CLAVE, first_name="Ana")

    def test_el_ingreso_enlaza_a_recuperar_la_contrasena(self):
        self.assertContains(self.client.get(reverse("cuentas:login")), reverse("cuentas:password_reset"))

    def test_envia_el_enlace_y_permite_crear_una_contrasena_nueva(self):
        respuesta = self.client.post(reverse("cuentas:password_reset"), {"email": "ana@correo.com"})
        self.assertRedirects(respuesta, reverse("cuentas:password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        correo = mail.outbox[0]
        self.assertEqual(correo.to, ["ana@correo.com"])
        self.assertIn("Restablece tu contraseña", correo.subject)
        enlace = re.search(r"http://testserver(/cuentas/contrasena/restablecer/\S+/)", correo.body).group(1)

        # Django cambia el token por «set-password» en la dirección para que no quede en el historial
        formulario = self.client.get(enlace, follow=True)
        self.assertContains(formulario, "Crea una contraseña nueva")
        respuesta = self.client.post(formulario.redirect_chain[-1][0],
                                     {"new_password1": NUEVA, "new_password2": NUEVA})
        self.assertRedirects(respuesta, reverse("cuentas:password_reset_complete"))
        self.assertTrue(self.client.login(username="ana@correo.com", password=NUEVA))

        # El enlace sirve una sola vez
        self.client.logout()
        self.assertContains(self.client.get(enlace, follow=True), "El enlace ya no sirve")

    def test_un_correo_no_registrado_no_recibe_nada_y_no_se_revela(self):
        respuesta = self.client.post(reverse("cuentas:password_reset"), {"email": "nadie@correo.com"})
        self.assertRedirects(respuesta, reverse("cuentas:password_reset_done"))
        self.assertEqual(len(mail.outbox), 0)

    def test_la_contrasena_nueva_cumple_las_mismas_reglas(self):
        self.client.post(reverse("cuentas:password_reset"), {"email": "ana@correo.com"})
        enlace = re.search(r"http://testserver(\S+)", mail.outbox[0].body).group(1)
        formulario = self.client.get(enlace, follow=True)
        respuesta = self.client.post(formulario.redirect_chain[-1][0],
                                     {"new_password1": "12345678", "new_password2": "12345678"})
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(self.client.login(username="ana@correo.com", password=CLAVE))


class CambiarContrasenaTests(TestCase):
    def setUp(self):
        self.ana = Usuario.objects.create_user(username="ana@correo.com", email="ana@correo.com",
                                               password=CLAVE, first_name="Ana")

    def test_pide_iniciar_sesion(self):
        respuesta = self.client.get(reverse("cuentas:password_change"))
        self.assertRedirects(respuesta, f"{reverse('cuentas:login')}?next={reverse('cuentas:password_change')}")

    def test_cambia_la_contrasena_y_mantiene_la_sesion(self):
        self.client.login(username="ana@correo.com", password=CLAVE)
        respuesta = self.client.post(reverse("cuentas:password_change"), {
            "old_password": CLAVE, "new_password1": NUEVA, "new_password2": NUEVA})
        self.assertRedirects(respuesta, reverse("cuentas:password_change_done"))
        self.assertContains(self.client.get(reverse("cuentas:mis_votos")), "Ana")
        self.ana.refresh_from_db()
        self.assertTrue(self.ana.check_password(NUEVA))

    def test_rechaza_si_la_contrasena_actual_no_coincide(self):
        self.client.login(username="ana@correo.com", password=CLAVE)
        respuesta = self.client.post(reverse("cuentas:password_change"), {
            "old_password": "otra-cosa", "new_password1": NUEVA, "new_password2": NUEVA})
        self.assertEqual(respuesta.status_code, 200)
        self.ana.refresh_from_db()
        self.assertTrue(self.ana.check_password(CLAVE))


class SesionYErroresTests(TestCase):
    def setUp(self):
        Usuario.objects.create_user(username="ana@correo.com", email="ana@correo.com", password=CLAVE, first_name="Ana")

    def test_saluda_al_ingresar_y_avisa_al_salir(self):
        respuesta = self.client.post(reverse("cuentas:login"), {"username": "ana@correo.com", "password": CLAVE},
                                     follow=True)
        self.assertContains(respuesta, "Hola, Ana")
        respuesta = self.client.post(reverse("cuentas:logout"), follow=True)
        self.assertContains(respuesta, "Cerraste tu sesión")

    def test_con_sesion_iniciada_el_ingreso_lleva_al_inicio(self):
        self.client.login(username="ana@correo.com", password=CLAVE)
        self.assertRedirects(self.client.get(reverse("cuentas:login")), reverse("votaciones:inicio"))

    def test_sin_edicion_activa_ninguna_pagina_falla(self):
        self.client.login(username="ana@correo.com", password=CLAVE)
        for nombre in ("votaciones:inicio", "votaciones:categorias", "votaciones:lista", "votaciones:resultados",
                       "cuentas:mis_votos", "cuentas:password_change"):
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 200, nombre)

    def test_pagina_404_propia(self):
        respuesta = self.client.get("/esta-pagina-no-existe/")
        self.assertEqual(respuesta.status_code, 404)
        self.assertContains(respuesta, "No encontramos esta página", status_code=404)
