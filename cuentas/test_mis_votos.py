"""
Pruebas de la página «Mis votos» (CP-07 de la Entrega 3).
Ejecutar:  python manage.py test cuentas.test_mis_votos -v 2
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from votaciones.servicios import registrar_voto
from votaciones.test_votos import CLAVE, crear_datos, opcion

Usuario = get_user_model()


class MisVotosTests(TestCase):
    def setUp(self):
        crear_datos(self)      # edición con las categorías Música y Desfile, y sus votaciones
        self.url = reverse("cuentas:mis_votos")

    def test_cp07_sin_sesion_se_pide_ingresar(self):
        respuesta = self.client.get(self.url)
        self.assertRedirects(respuesta, f"{reverse('cuentas:login')}?next={self.url}")

    def test_cp07_muestra_los_votos_del_usuario_con_su_comprobante(self):
        voto = registrar_voto(self.usuario, self.cancion, opcion(self.cancion, 1).pk)
        self.client.force_login(self.usuario)
        respuesta = self.client.get(self.url)
        self.assertContains(respuesta, "Cancion B")
        self.assertContains(respuesta, voto.comprobante)
        self.assertContains(respuesta, "Has votado en 1 de 2 categorías")

    def test_cp07_las_categorias_sin_voto_aparecen_como_pendientes(self):
        registrar_voto(self.usuario, self.cancion, opcion(self.cancion, 0).pk)
        self.client.force_login(self.usuario)
        respuesta = self.client.get(self.url)
        self.assertEqual([c.nombre for c in respuesta.context["pendientes"]], ["Desfile"])

    def test_cp07_sin_votos_lo_indica(self):
        self.client.force_login(self.usuario)
        respuesta = self.client.get(self.url)
        self.assertContains(respuesta, "Todavía no has votado en esta edición.")

    def test_cp07_no_muestra_los_votos_de_otro_usuario(self):
        otro = Usuario.objects.create_user(username="beto", email="beto@ejemplo.com", password=CLAVE)
        voto_de_otro = registrar_voto(otro, self.cancion, opcion(self.cancion, 0).pk)
        self.client.force_login(self.usuario)
        respuesta = self.client.get(self.url)
        self.assertNotContains(respuesta, voto_de_otro.comprobante)
        self.assertEqual(respuesta.context["votos"], [])

    def test_cp04_el_ingreso_avisa_que_hay_que_iniciar_sesion_para_votar(self):
        respuesta = self.client.get(f"{reverse('cuentas:login')}?next={self.cancion.get_absolute_url()}")
        self.assertContains(respuesta, "Para votar debes iniciar sesión")
