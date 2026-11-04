"""
Registro de votos. Todas las reglas de la Entrega 3 se validan aquí, en el servidor,
antes de guardar en MySQL. Las vistas solo llaman a validar_voto() y registrar_voto(),
así la misma regla se aplica venga la solicitud de donde venga.

Orden de las validaciones:
  1. El usuario inició sesión.
  2. La votación está habilitada: visible, de una categoría visible y de la edición activa.
  3. La votación está abierta (no está próxima ni cerrada).
  4. La opción existe, está activa y pertenece a esa votación.
  5. El usuario no ha votado antes según la regla de la categoría: por defecto, un solo voto
     en toda la categoría (regla de la guía); si el administrador lo configura, uno por votación.
Si dos solicitudes llegan al mismo tiempo, la restricción única de la tabla de votos
deja guardar solo una (ver registrar_voto).
"""
from django.db import IntegrityError, transaction
from django.utils.timezone import localtime

from .models import Edicion, Opcion, Votacion, Voto


class VotoRechazado(Exception):
    """El voto no cumple una regla. El mensaje se le muestra tal cual al usuario."""


class VotoDuplicado(VotoRechazado):
    """El usuario ya tiene un voto en esa categoría de la edición."""


def voto_que_bloquea(usuario, votacion):
    """
    El voto que ya impide al usuario votar en esa votación, o None si todavía puede votar.
    Regla por defecto: cualquier voto suyo en la categoría. Regla «un voto en cada votación»:
    solo un voto suyo en esa misma votación.
    """
    if not usuario.is_authenticated:
        return None
    categoria = votacion.categoria
    votos = Voto.objects.select_related("opcion", "votacion", "categoria").filter(
        usuario=usuario, edicion=categoria.edicion_id, categoria=categoria)
    if not categoria.un_voto_por_categoria:
        votos = votos.filter(votacion=votacion)
    return votos.first()


def mensaje_duplicado(voto):
    if voto.categoria.un_voto_por_categoria:
        return (f"Ya votaste en la categoría «{voto.categoria.nombre}» por «{voto.opcion.nombre}». "
                "En esta categoría se permite un solo voto por edición.")
    return (f"Ya votaste en «{voto.votacion.nombre}» por «{voto.opcion.nombre}». "
            "En esta categoría se permite un voto en cada votación.")


def validar_voto(usuario, votacion, opcion_id):
    """Comprueba todas las reglas y devuelve la opción elegida. Lanza VotoRechazado si algo falla."""
    if not usuario.is_authenticated:
        raise VotoRechazado("Debes iniciar sesión para votar.")

    categoria = votacion.categoria
    if not (votacion.visible and categoria.visible) or categoria.edicion_id != getattr(Edicion.objects.activa(), "pk", None):
        raise VotoRechazado("Esta votación no está habilitada para recibir votos.")

    estado = votacion.estado
    if estado == Votacion.Estado.PROXIMA:
        raise VotoRechazado(f"La votación «{votacion.nombre}» todavía no está abierta. "
                            f"Abre el {localtime(votacion.fecha_apertura):%d/%m/%Y a las %I:%M %p}.")
    if estado == Votacion.Estado.CERRADA:
        raise VotoRechazado(f"La votación «{votacion.nombre}» ya cerró y no recibe más votos.")

    if not opcion_id:
        raise VotoRechazado("Elige una opción antes de continuar.")
    try:
        opcion = votacion.opciones.get(pk=int(opcion_id), activa=True)
    except (Opcion.DoesNotExist, ValueError, TypeError):
        raise VotoRechazado("La opción enviada no pertenece a esta votación.") from None

    voto_anterior = voto_que_bloquea(usuario, votacion)
    if voto_anterior:
        raise VotoDuplicado(mensaje_duplicado(voto_anterior))
    return opcion


def registrar_voto(usuario, votacion, opcion_id):
    """Valida otra vez todas las reglas y guarda el voto en MySQL. Devuelve el Voto creado."""
    opcion = validar_voto(usuario, votacion, opcion_id)
    try:
        with transaction.atomic():
            return Voto.objects.create(usuario=usuario, opcion=opcion)
    except IntegrityError:
        # Dos solicitudes simultáneas pasaron la validación anterior al mismo tiempo.
        # La restricción única «voto_unico_usuario_categoria_edicion» de MySQL dejó
        # guardar solo la primera; esta se rechaza como voto duplicado.
        voto_anterior = voto_que_bloquea(usuario, votacion)
        if voto_anterior is None:
            raise
        raise VotoDuplicado(mensaje_duplicado(voto_anterior)) from None
