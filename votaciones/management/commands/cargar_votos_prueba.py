"""
Carga votos de prueba para que la página de resultados tenga datos que mostrar.

Uso:  python manage.py cargar_votos_prueba
      python manage.py cargar_votos_prueba --votantes 60 --semilla 7

Crea votantes ficticios (votante01@ejemplo.com, votante02@ejemplo.com, …) sin contraseña
utilizable, de modo que nadie puede ingresar con ellos, y les registra votos en las
votaciones visibles de la edición activa que ya abrieron (abiertas o cerradas). Respeta la
regla de cada categoría y la restricción única de la tabla de votos. La fecha de cada voto
queda dentro del periodo en que la votación estuvo abierta.

Se puede ejecutar varias veces: un votante que ya votó en una categoría no vuelve a votar.
Ejecútalo después de cargar_datos_prueba. No toca los votos de los usuarios reales.
"""
import random
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from votaciones.models import Edicion, Votacion, Voto
from votaciones.servicios import voto_que_bloquea

Usuario = get_user_model()


class Command(BaseCommand):
    help = "Registra votos de votantes ficticios en las votaciones de la edición activa."

    def add_arguments(self, parser):
        parser.add_argument("--votantes", type=int, default=40, help="Cuántos votantes ficticios usar (por defecto 40).")
        parser.add_argument("--semilla", type=int, default=2027, help="Semilla para repetir los mismos votos.")

    @transaction.atomic
    def handle(self, *args, votantes, semilla, **opciones):
        if not 1 <= votantes <= 500:
            raise CommandError("El número de votantes debe estar entre 1 y 500.")
        edicion = Edicion.objects.activa()
        if edicion is None:
            raise CommandError("No hay una edición activa. Ejecuta primero: python manage.py cargar_datos_prueba")

        ahora = timezone.now()
        azar = random.Random(semilla)
        votaciones = [v for v in (Votacion.objects.de_edicion(edicion).visibles()
                                  .filter(es_prueba=False, fecha_apertura__lte=ahora)
                                  .select_related("categoria").prefetch_related("opciones")
                                  .order_by("categoria__orden", "orden"))
                      if any(o.activa for o in v.opciones.all())]
        if not votaciones:
            raise CommandError("La edición activa no tiene votaciones abiertas o cerradas con opciones.")

        # Cada votación tiene sus «preferidos»: pesos distintos por opción, para que los
        # resultados no salgan parejos y se vea quién va ganando.
        pesos = {}
        for votacion in votaciones:
            activas = [o for o in votacion.opciones.all() if o.activa]
            base = [7, 5, 3, 2, 1, 1, 1, 1][:len(activas)] + [1] * max(0, len(activas) - 8)
            azar.shuffle(base)
            pesos[votacion.pk] = (activas, base)

        por_categoria = {}
        for votacion in votaciones:
            por_categoria.setdefault(votacion.categoria, []).append(votacion)

        creados = existentes = 0
        for numero in range(1, votantes + 1):
            correo = f"votante{numero:02d}@ejemplo.com"
            votante, nuevo = Usuario.objects.get_or_create(
                email=correo,
                defaults={"username": correo, "first_name": "Votante", "last_name": f"de prueba {numero:02d}",
                          "acepta_tratamiento_datos": True, "fecha_aceptacion_datos": ahora},
            )
            if nuevo:
                votante.set_unusable_password()   # nadie puede ingresar con estas cuentas
                votante.save(update_fields=["password"])

            for categoria, lista in por_categoria.items():
                if azar.random() > 0.85:          # no todos votan en todas las categorías
                    continue
                elegidas = [azar.choice(lista)] if categoria.un_voto_por_categoria else lista
                for votacion in elegidas:
                    # Se sortean la opción y el momento antes de revisar si ya votó, para que
                    # cada ejecución con la misma semilla tome exactamente las mismas decisiones.
                    activas, base = pesos[votacion.pk]
                    opcion = azar.choices(activas, weights=base)[0]
                    momento = azar.random()
                    if voto_que_bloquea(votante, votacion):
                        existentes += 1
                        continue
                    voto = Voto.objects.create(usuario=votante, opcion=opcion)
                    # La fecha del voto queda dentro del periodo en que la votación estuvo abierta.
                    fin = min(votacion.fecha_cierre, ahora)
                    duracion = max((fin - votacion.fecha_apertura).total_seconds(), 1)
                    Voto.objects.filter(pk=voto.pk).update(
                        fecha=votacion.fecha_apertura + timedelta(seconds=int(momento * duracion)))
                    creados += 1

        self.stdout.write(self.style.SUCCESS(
            f"Votos de prueba: {creados} nuevos de {votantes} votantes ficticios"
            f"{f' ({existentes} ya estaban registrados)' if existentes else ''}. "
            "Revisa la página Resultados."
        ))
