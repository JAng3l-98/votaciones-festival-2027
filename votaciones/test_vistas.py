"""Pruebas de la interfaz pública.  Ejecutar: python manage.py test votaciones"""
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, Edicion, Opcion, Votacion


class InterfazPublicaTests(TestCase):
    def setUp(self):
        ahora = timezone.now()
        edicion = Edicion.objects.create(nombre="Festival 2027", anio=2027, numero=60, activa=True)
        self.musica = Categoria.objects.create(edicion=edicion, nombre="Música", slug="musica")
        self.desfile = Categoria.objects.create(edicion=edicion, nombre="Desfile y comparsas", slug="desfile")
        Categoria.objects.create(edicion=edicion, nombre="Categoría oculta", slug="oculta", visible=False)
        self.cancion = Votacion.objects.create(
            categoria=self.musica, nombre="Canción favorita del público", slug="cancion",
            fecha_apertura=ahora - timedelta(days=1), fecha_cierre=ahora + timedelta(days=5))
        self.comparsa = Votacion.objects.create(
            categoria=self.desfile, nombre="Comparsa más alegre", slug="comparsa",
            fecha_apertura=ahora + timedelta(days=3), fecha_cierre=ahora + timedelta(days=6))
        self.oculta = Votacion.objects.create(
            categoria=self.musica, nombre="Votación oculta", slug="oculta", visible=False,
            fecha_apertura=ahora - timedelta(days=1), fecha_cierre=ahora + timedelta(days=5))
        Opcion.objects.create(votacion=self.cancion, nombre="Brisa del Valle")
        Opcion.objects.create(votacion=self.cancion, nombre="Opción retirada", activa=False)

    def test_categorias_muestra_solo_las_visibles(self):
        respuesta = self.client.get(reverse("votaciones:categorias"))
        self.assertContains(respuesta, "Música")
        self.assertContains(respuesta, "Desfile y comparsas")
        self.assertNotContains(respuesta, "Categoría oculta")

    def test_lista_agrupa_por_estado_y_oculta_lo_no_visible(self):
        respuesta = self.client.get(reverse("votaciones:lista"))
        self.assertContains(respuesta, "Canción favorita del público")
        self.assertContains(respuesta, "Próximamente")
        self.assertNotContains(respuesta, "Votación oculta")

    def test_filtro_por_categoria(self):
        respuesta = self.client.get(reverse("votaciones:lista"), {"categoria": "musica"})
        self.assertContains(respuesta, "Canción favorita del público")
        self.assertNotContains(respuesta, "Comparsa más alegre")

    def test_detalle_muestra_solo_las_opciones_activas(self):
        respuesta = self.client.get(reverse("votaciones:detalle", args=[self.cancion.pk]))
        self.assertContains(respuesta, "Brisa del Valle")
        self.assertNotContains(respuesta, "Opción retirada")

    def test_una_votacion_oculta_no_se_puede_abrir(self):
        respuesta = self.client.get(reverse("votaciones:detalle", args=[self.oculta.pk]))
        self.assertEqual(respuesta.status_code, 404)

    def test_el_inicio_muestra_las_votaciones_abiertas(self):
        respuesta = self.client.get(reverse("votaciones:inicio"))
        self.assertContains(respuesta, "Votaciones abiertas")
        self.assertContains(respuesta, "Canción favorita del público")
