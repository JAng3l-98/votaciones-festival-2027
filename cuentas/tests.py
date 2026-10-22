from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class AutenticacionTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username="ana", email="ana@correo.com", password="Clave-segura-2027", first_name="Ana")

    def test_la_contrasena_se_guarda_cifrada(self):
        self.assertNotEqual(self.usuario.password, "Clave-segura-2027")
        self.assertTrue(self.usuario.check_password("Clave-segura-2027"))

    def test_ingresar_con_correo_y_salir(self):
        respuesta = self.client.post(reverse("cuentas:login"), {"username": "ana@correo.com", "password": "Clave-segura-2027"})
        self.assertRedirects(respuesta, reverse("votaciones:inicio"))
        self.assertContains(self.client.get(reverse("votaciones:inicio")), "Salir")
        self.client.post(reverse("cuentas:logout"))
        self.assertContains(self.client.get(reverse("votaciones:inicio")), "Ingresar")
