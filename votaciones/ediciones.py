"""
Preparar una nueva edición del Festival sin tocar el código (entrega final).

duplicar_edicion() copia una edición completa al año siguiente: sus categorías, sus
votaciones con las fechas corridas un año y sus opciones. No copia votos. La edición
nueva queda inactiva para que la Fundación la revise (participantes, fechas, imágenes)
y la active cuando esté lista; mientras tanto el público sigue viendo la edición actual.
"""
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Categoria, Edicion, Opcion, Votacion


def un_anio_despues(valor):
    """La misma fecha (u hora) un año después. El 29 de febrero pasa al 28."""
    if valor is None:
        return None
    try:
        return valor.replace(year=valor.year + 1)
    except ValueError:
        return valor.replace(year=valor.year + 1, day=28)


@transaction.atomic
def duplicar_edicion(edicion):
    """Crea la edición del año siguiente a partir de `edicion` y devuelve (nueva, totales)."""
    anio = edicion.anio + 1
    if Edicion.objects.filter(anio=anio).exists():
        raise ValidationError(f"Ya existe la edición {anio}: no se duplicó {edicion}.")

    nombre = (edicion.nombre.replace(str(edicion.anio), str(anio)) if str(edicion.anio) in edicion.nombre
              else f"{edicion.nombre} {anio}")
    nueva = Edicion.objects.create(
        nombre=nombre, anio=anio, numero=edicion.numero + 1 if edicion.numero else None,
        fecha_inicio=un_anio_despues(edicion.fecha_inicio), fecha_fin=un_anio_despues(edicion.fecha_fin),
        descripcion=edicion.descripcion, activa=False,
    )
    totales = {"categorias": 0, "votaciones": 0, "opciones": 0}
    for categoria in edicion.categorias.all():
        copia_categoria = Categoria.objects.create(
            edicion=nueva, nombre=categoria.nombre, slug=categoria.slug, descripcion=categoria.descripcion,
            orden=categoria.orden, visible=categoria.visible, regla_voto=categoria.regla_voto,
        )
        totales["categorias"] += 1
        for votacion in categoria.votaciones.all():
            copia_votacion = Votacion.objects.create(
                categoria=copia_categoria, nombre=votacion.nombre, slug=votacion.slug,
                descripcion=votacion.descripcion, imagen=votacion.imagen.name,
                fecha_apertura=un_anio_despues(votacion.fecha_apertura),
                fecha_cierre=un_anio_despues(votacion.fecha_cierre),
                publicacion_resultados=votacion.publicacion_resultados,
                audiencia_resultados=votacion.audiencia_resultados,
                es_prueba=votacion.es_prueba, visible=votacion.visible, orden=votacion.orden,
            )
            totales["votaciones"] += 1
            Opcion.objects.bulk_create(
                Opcion(votacion=copia_votacion, nombre=opcion.nombre, descripcion=opcion.descripcion,
                       imagen=opcion.imagen.name, orden=opcion.orden, activa=opcion.activa)
                for opcion in votacion.opciones.all()
            )
            totales["opciones"] += votacion.opciones.count()
    return nueva, totales
