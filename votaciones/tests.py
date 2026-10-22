"""Pruebas automáticas de los modelos y de las páginas públicas.  Ejecutar: python manage.py test"""
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, Edicion, Opcion, Votacion


class ModelosTests(TestCase):
    def setUp(self):
        self.edicion = Edicion.objects.create(nombre="Festival 2027", anio=2027, numero=60, activa=True)
        self.categoria = Categoria.objects.create(edicion=self.edicion, nombre="Música", slug="musica")
        ahora = timezone.now()
        self.votacion = Votacion.objects.create(
            categoria=self.categoria, nombre="Canción favorita del público", slug="cancion-favorita",
            fecha_apertura=ahora - timedelta(days=1), fecha_cierre=ahora + timedelta(days=1))

    def test_jerarquia_edicion_categoria_votacion_opcion(self):
        opcion = Opcion.objects.create(votacion=self.votacion, nombre="Canción A")
        self.assertEqual(opcion.votacion.categoria.edicion, self.edicion)
        self.assertEqual(self.edicion.categorias.count(), 1)
        self.assertEqual(self.categoria.votaciones.count(), 1)

    def test_estado_segun_fechas(self):
        ahora = timezone.now()
        self.assertEqual(self.votacion.estado, Votacion.Estado.ABIERTA)
        self.votacion.fecha_apertura, self.votacion.fecha_cierre = ahora + timedelta(days=1), ahora + timedelta(days=2)
        self.assertEqual(self.votacion.estado, Votacion.Estado.PROXIMA)
        self.votacion.fecha_apertura, self.votacion.fecha_cierre = ahora - timedelta(days=2), ahora - timedelta(days=1)
        self.assertEqual(self.votacion.estado, Votacion.Estado.CERRADA)

    def test_solo_una_edicion_activa(self):
        Edicion.objects.create(nombre="Festival 2028", anio=2028, activa=True)
        self.edicion.refresh_from_db()
        self.assertFalse(self.edicion.activa)
        self.assertEqual(Edicion.objects.activa().anio, 2028)

    def test_sin_edicion_activa_se_muestra_la_mas_reciente(self):
        Edicion.objects.update(activa=False)
        Edicion.objects.create(nombre="Festival 2026", anio=2026)
        self.assertEqual(Edicion.objects.activa().anio, 2027)

    def test_cierre_antes_de_la_apertura_no_es_valido(self):
        ahora = timezone.now()
        votacion = Votacion(categoria=self.categoria, nombre="Mal configurada", slug="mal",
                            fecha_apertura=ahora, fecha_cierre=ahora - timedelta(hours=1))
        with self.assertRaises(ValidationError):
            votacion.full_clean()

    def test_no_se_borra_una_edicion_con_categorias(self):
        with self.assertRaises(ProtectedError):
            self.edicion.delete()


class PaginasPublicasTests(TestCase):
    def test_paginas_responden(self):
        for nombre in ("votaciones:inicio", "votaciones:categorias", "votaciones:lista"):
            self.assertEqual(self.client.get(reverse(nombre)).status_code, 200, nombre)

    def test_inicio_muestra_la_edicion_registrada(self):
        Edicion.objects.create(nombre="Festival 2027", anio=2027, numero=60, activa=True)
        respuesta = self.client.get(reverse("votaciones:inicio"))
        self.assertContains(respuesta, "Festival 2027")
        self.assertContains(respuesta, "Edición 60")
