"""Pruebas de la administración.  Ejecutar: python manage.py test votaciones"""
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Votacion


class AdministracionTests(TestCase):
    def setUp(self):
        administrador = get_user_model().objects.create_superuser(
            username="admin", email="admin@ejemplo.com", password="Clave-de-prueba-2027")
        self.client.force_login(administrador)
        call_command("cargar_datos_prueba", verbosity=0)

    def test_las_listas_del_admin_responden(self):
        for modelo in ("edicion", "categoria", "votacion", "opcion"):
            respuesta = self.client.get(reverse(f"admin:votaciones_{modelo}_changelist"))
            self.assertEqual(respuesta.status_code, 200, modelo)

    def test_la_votacion_muestra_sus_opciones_y_reglas(self):
        votacion = Votacion.objects.get(nombre="Canción favorita del público")
        respuesta = self.client.get(reverse("admin:votaciones_votacion_change", args=[votacion.pk]))
        self.assertContains(respuesta, "Brisa del Valle")
        self.assertContains(respuesta, "Reglas configurables")

    def test_busqueda_de_votaciones(self):
        respuesta = self.client.get(reverse("admin:votaciones_votacion_changelist"), {"q": "Comparsa"})
        self.assertContains(respuesta, "Comparsa más alegre del desfile")
        self.assertNotContains(respuesta, "Canción favorita del público")
