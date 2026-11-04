"""
Prueba de concurrencia (CP-09): envía al mismo tiempo varias solicitudes POST de voto
del mismo usuario a votaciones de una misma categoría y muestra cuántos votos quedan.

Uso:  python manage.py probar_concurrencia correo@ejemplo.com
      python manage.py probar_concurrencia correo@ejemplo.com --solicitudes 5

Cada solicitud corre en su propio hilo y con su propia conexión a MySQL, como si fueran
dos pestañas que pulsan «Confirmar voto» en el mismo instante. Pasan por la misma ruta,
la misma vista y las mismas validaciones que el sitio. Se usa una votación abierta
en la que el usuario todavía puede votar; el voto que quede registrado es real.
"""
import threading

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.test import Client
from django.urls import reverse

from votaciones.models import Edicion, Votacion, Voto
from votaciones.servicios import voto_que_bloquea


class Command(BaseCommand):
    help = "Envía solicitudes de voto simultáneas a una misma categoría y verifica que solo quede un voto (CP-09)."

    def add_arguments(self, parser):
        parser.add_argument("correo", help="Correo de un usuario registrado (el votante de prueba).")
        parser.add_argument("--solicitudes", type=int, default=2, help="Cuántas solicitudes simultáneas enviar (2 por defecto).")

    def handle(self, correo, solicitudes, **opciones):
        usuario = get_user_model().objects.filter(email__iexact=correo).first()
        if usuario is None:
            raise CommandError(f"No hay ningún usuario con el correo {correo}. Regístralo primero en el sitio.")
        edicion = Edicion.objects.activa()
        candidatas = (Votacion.objects.de_edicion(edicion).visibles().abiertas()
                      .filter(opciones__activa=True).distinct()
                      .select_related("categoria").order_by("categoria__orden", "orden"))
        votacion = next((v for v in candidatas if voto_que_bloquea(usuario, v) is None), None)
        if votacion is None:
            raise CommandError("Ese usuario ya no puede votar en ninguna votación abierta. Usa otro usuario.")
        opciones_validas = list(votacion.opciones.filter(activa=True))
        categoria = votacion.categoria
        # Votos que cuentan para la regla: los de la categoría (regla por defecto) o los de la votación.
        if categoria.un_voto_por_categoria:
            alcance, votos_del_alcance = "la categoría", Voto.objects.filter(usuario=usuario, categoria=categoria)
        else:
            alcance, votos_del_alcance = "la votación", Voto.objects.filter(usuario=usuario, votacion=votacion)

        self.stdout.write(f"Usuario: {usuario.email}")
        self.stdout.write(f"Categoría: {categoria.nombre} · Votación: {votacion.nombre}")
        self.stdout.write(f"Regla de la categoría: {categoria.get_regla_voto_display()}")
        self.stdout.write(f"Votos de este usuario en {alcance} ANTES: {votos_del_alcance.count()}")
        self.stdout.write(f"Enviando {solicitudes} solicitudes POST al mismo tiempo a {reverse('votaciones:votar', args=[votacion.pk])} …\n")

        barrera = threading.Barrier(solicitudes)
        resultados = [None] * solicitudes

        def enviar(numero):
            elegida = opciones_validas[numero % len(opciones_validas)]
            cliente = Client(HTTP_HOST="127.0.0.1")           # cada hilo es un navegador distinto
            cliente.force_login(usuario)
            try:
                barrera.wait()                                 # todas salen en el mismo instante
                respuesta = cliente.post(reverse("votaciones:votar", args=[votacion.pk]), {"opcion": elegida.pk})
                aceptada = "/votos/" in respuesta.get("Location", "")
                resultados[numero] = (elegida.nombre, "VOTO REGISTRADO" if aceptada else "RECHAZADA (voto duplicado)")
            finally:
                connection.close()                             # cada hilo cierra su conexión a MySQL

        hilos = [threading.Thread(target=enviar, args=(n,)) for n in range(solicitudes)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join()

        for numero, (nombre, resultado) in enumerate(resultados, start=1):
            self.stdout.write(f"  Solicitud {numero} (opción «{nombre}»): {resultado}")
        total = votos_del_alcance.count()
        estilo = self.style.SUCCESS if total == 1 else self.style.ERROR
        self.stdout.write(estilo(f"\nVotos de este usuario en {alcance} DESPUÉS: {total}"
                                 + (" → la regla se cumplió: solo quedó un voto." if total == 1 else " → ¡revisar!")))
