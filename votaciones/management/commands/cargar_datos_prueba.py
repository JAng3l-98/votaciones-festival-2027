from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from votaciones.models import Edicion, Categoria, Votacion, Opcion


class Command(BaseCommand):
    help = "Carga datos de prueba del Festival sin duplicar registros."

    @transaction.atomic
    def handle(self, *args, **options):
        ahora = timezone.now()

        with transaction.atomic():
            edicion, creada = Edicion.objects.get_or_create(
                anio=2027,
                defaults={
                    "nombre": "Festival de la Leyenda Vallenata 2027",
                    "numero": 60,
                    "fecha_inicio": "2027-04-29",
                    "fecha_fin": "2027-05-02",
                    "descripcion": "Edicion de prueba del Festival.",
                    "activa": True,
                },
            )

            if creada:
                self.stdout.write("Edicion creada.")
            else:
                self.stdout.write("La edicion ya existia.")

            datos_categorias = [
                ("Acordeon profesional", "acordeon-profesional"),
                ("Cancion inedita", "cancion-inedita"),
                ("Piqueria", "piqueria"),
                ("Conjunto tipico", "conjunto-tipico"),
            ]

            categorias = []

            for orden, (nombre, slug) in enumerate(datos_categorias, start=1):
                categoria, _ = Categoria.objects.get_or_create(
                    edicion=edicion,
                    slug=slug,
                    defaults={
                        "nombre": nombre,
                        "descripcion": f"Categoria de prueba: {nombre}.",
                        "orden": orden,
                        "visible": True,
                    },
                )
                categorias.append(categoria)

            datos_votaciones = [
                ("Rey vallenato - ronda 1", "rey-ronda-1", 0),
                ("Rey vallenato - ronda 2", "rey-ronda-2", 0),
                ("Mejor cancion inedita", "mejor-cancion-inedita", 1),
                ("Mejor interprete de piqueria", "mejor-piqueria", 2),
                ("Mejor conjunto tipico", "mejor-conjunto-tipico", 3),
                ("Favorito del publico", "favorito-publico", 1),
            ]

            nombres_opciones = [
                ("Participante de prueba A", "Primera opcion de demostracion."),
                ("Participante de prueba B", "Segunda opcion de demostracion."),
                ("Participante de prueba C", "Tercera opcion de demostracion."),
            ]

            for orden, (nombre, slug, indice_categoria) in enumerate(
                datos_votaciones, start=1
            ):
                votacion, _ = Votacion.objects.get_or_create(
                    categoria=categorias[indice_categoria],
                    slug=slug,
                    defaults={
                        "nombre": nombre,
                        "descripcion": "Votacion de demostracion.",
                        "fecha_apertura": ahora - timedelta(days=1),
                        "fecha_cierre": ahora + timedelta(days=30),
                        "votos_por_usuario": 1,
                        "publicacion_resultados": Votacion.Publicacion.AL_CIERRE,
                        "es_prueba": True,
                        "visible": True,
                        "orden": orden,
                    },
                )

                for orden_opcion, (nombre_opcion, descripcion) in enumerate(
                    nombres_opciones, start=1
                ):
                    Opcion.objects.get_or_create(
                        votacion=votacion,
                        nombre=nombre_opcion,
                        defaults={
                            "descripcion": descripcion,
                            "orden": orden_opcion,
                            "activa": True,
                        },
                    )

        self.stdout.write(self.style.SUCCESS(
            "Carga finalizada. Resumen de registros:"
        ))
        self.stdout.write(f"Ediciones: {Edicion.objects.count()}")
        self.stdout.write(f"Categorias: {Categoria.objects.count()}")
        self.stdout.write(f"Votaciones: {Votacion.objects.count()}")
        self.stdout.write(f"Opciones: {Opcion.objects.count()}")
