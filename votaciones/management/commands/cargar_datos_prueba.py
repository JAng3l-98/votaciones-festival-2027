"""
Carga datos de prueba: la edición 2027, cuatro categorías, seis votaciones y sus opciones.

Uso:  python manage.py cargar_datos_prueba

Se puede ejecutar varias veces: si un dato ya existe, lo actualiza en lugar de duplicarlo.
Son datos inventados para probar el sistema; no son finalistas reales del Festival.
"""
from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from votaciones.models import Categoria, Edicion, Opcion, Votacion

BOGOTA = ZoneInfo("America/Bogota")


def fecha(texto):
    """Convierte «2027-04-30 23:59» en una fecha con la hora de Colombia."""
    return datetime.strptime(texto, "%Y-%m-%d %H:%M").replace(tzinfo=BOGOTA)


CATEGORIAS = [
    # (identificador, nombre, descripción)
    ("musica", "Música", "Canciones, intérpretes y agrupaciones."),
    ("desfile-y-comparsas", "Desfile y comparsas", "Comparsas y presentaciones del desfile."),
    ("piloneras", "Piloneras", "Vestuario y baile del desfile de Piloneras."),
    ("reconocimientos-del-publico", "Reconocimientos del público", "Distinciones que entrega el público."),
]

VOTACIONES = [
    # (categoría, nombre, apertura, cierre, publicación de resultados, de prueba, visible, opciones)
    ("musica", "Canción favorita del público", "2026-10-01 08:00", "2027-04-30 23:59", "al_cierre", False, True,
     ["Brisa del Valle", "Acordeón de mi tierra", "Noches del Cesar", "Camino de la Sierra"]),
    ("musica", "Agrupación favorita del público", "2026-10-01 08:00", "2027-04-30 23:59", "al_cierre", False, True,
     ["Agrupación Aurora", "Agrupación Horizonte", "Agrupación Sabana"]),
    ("desfile-y-comparsas", "Comparsa más alegre del desfile", "2026-10-15 08:00", "2027-04-28 23:59", "en_vivo", False, True,
     ["Comparsa Colores del Valle", "Comparsa Alegría", "Comparsa Raíces"]),
    ("piloneras", "Mejor vestuario de Piloneras", "2027-04-26 08:00", "2027-04-29 23:59", "al_cierre", False, True,
     ["Grupo Pilón Dorado", "Grupo Tradición", "Grupo Maíz y Tambor"]),
    ("reconocimientos-del-publico", "Presentación más recordada", "2026-09-01 08:00", "2026-10-15 23:59", "al_cierre", False, True,
     ["Presentación de apertura", "Presentación de cierre", "Homenaje a los juglares"]),
    ("musica", "Votación de ensayo", "2026-10-01 08:00", "2027-04-30 23:59", "no_publicar", True, False,
     ["Opción de prueba 1", "Opción de prueba 2"]),
]


class Command(BaseCommand):
    help = "Carga datos de prueba de la edición 2027 (categorías, votaciones y opciones)."

    @transaction.atomic
    def handle(self, *args, **opciones):
        edicion, _ = Edicion.objects.update_or_create(
            anio=2027,
            defaults={
                "nombre": "Festival de la Leyenda Vallenata 2027",
                "numero": 60,
                "fecha_inicio": date(2027, 4, 28),
                "fecha_fin": date(2027, 5, 1),
                "descripcion": "Edición 60 del Festival. Datos de prueba.",
                "activa": True,
            },
        )

        categorias = {}
        for orden, (slug, nombre, descripcion) in enumerate(CATEGORIAS, start=1):
            categorias[slug], _ = Categoria.objects.update_or_create(
                edicion=edicion, slug=slug,
                defaults={"nombre": nombre, "descripcion": descripcion, "orden": orden, "visible": True},
            )

        total_opciones = 0
        for orden, (slug_categoria, nombre, apertura, cierre, publicacion, prueba, visible, nombres_opciones) in enumerate(VOTACIONES, start=1):
            votacion, _ = Votacion.objects.update_or_create(
                categoria=categorias[slug_categoria], nombre=nombre,
                defaults={
                    "slug": slugify(nombre),          # «Canción favorita…» → «cancion-favorita…»
                    "descripcion": f"Elige tu favorito en «{nombre}». Datos de prueba.",
                    "fecha_apertura": fecha(apertura),
                    "fecha_cierre": fecha(cierre),
                    "votos_por_usuario": 1,
                    "publicacion_resultados": publicacion,
                    "es_prueba": prueba,
                    "visible": visible,
                    "orden": orden,
                },
            )
            for orden_opcion, nombre_opcion in enumerate(nombres_opciones, start=1):
                Opcion.objects.update_or_create(
                    votacion=votacion, nombre=nombre_opcion,
                    defaults={"descripcion": "Dato de prueba.", "orden": orden_opcion, "activa": True},
                )
                total_opciones += 1

        if opciones["verbosity"] > 0:   # las pruebas automáticas lo llaman en silencio (verbosity=0)
            self.stdout.write(self.style.SUCCESS(
                f"Datos de prueba listos: edición {edicion.anio}, {len(CATEGORIAS)} categorías, "
                f"{len(VOTACIONES)} votaciones y {total_opciones} opciones."
            ))
