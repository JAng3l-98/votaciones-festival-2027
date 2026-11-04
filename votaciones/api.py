"""
API de consulta (Entrega 3).

GET /api/categorias/  → categorías de la edición activa con sus votaciones (subeventos)
y las opciones de cada una, leídas de MySQL y entregadas en JSON con JsonResponse.

Es de solo lectura: acepta únicamente GET y no entrega datos de usuarios ni votos.
Con ?edicion=2026 se consulta otra edición por su año.
"""
from django.db.models import Prefetch
from django.http import JsonResponse
from django.urls import reverse
from django.views.decorators.http import require_GET

from .models import Categoria, Edicion, Opcion, Votacion


def opcion_json(opcion):
    return {"id": opcion.pk, "nombre": opcion.nombre, "descripcion": opcion.descripcion, "orden": opcion.orden}


def votacion_json(request, votacion):
    return {
        "id": votacion.pk,
        "nombre": votacion.nombre,
        "estado": votacion.estado,                     # proxima, abierta o cerrada
        "abre": votacion.fecha_apertura.isoformat(),
        "cierra": votacion.fecha_cierre.isoformat(),
        "url": request.build_absolute_uri(reverse("votaciones:detalle", args=[votacion.pk])),
        "opciones": [opcion_json(o) for o in votacion.opciones.all()],
    }


@require_GET
def categorias(request):
    anio = request.GET.get("edicion")
    if anio:
        edicion = Edicion.objects.filter(anio=anio).first() if anio.isdigit() else None
        if edicion is None:
            return JsonResponse({"error": f"No existe la edición {anio}."}, status=404,
                                json_dumps_params={"ensure_ascii": False})
    else:
        edicion = Edicion.objects.activa()
    if edicion is None:
        return JsonResponse({"edicion": None, "total_categorias": 0, "categorias": []})

    # Cuatro consultas en total (edición, categorías, votaciones y opciones), sin importar
    # cuántos datos haya: prefetch_related trae cada nivel en una sola consulta.
    opciones = Opcion.objects.filter(activa=True)
    votaciones = Votacion.objects.filter(visible=True).prefetch_related(Prefetch("opciones", queryset=opciones))
    lista = (Categoria.objects.filter(edicion=edicion, visible=True)
             .prefetch_related(Prefetch("votaciones", queryset=votaciones)))

    datos = {
        "edicion": {"id": edicion.pk, "nombre": edicion.nombre, "anio": edicion.anio, "numero": edicion.numero},
        "total_categorias": len(lista),
        "categorias": [
            {
                "id": c.pk,
                "nombre": c.nombre,
                "slug": c.slug,
                "descripcion": c.descripcion,
                "regla_voto": c.regla_voto,           # categoria (un solo voto) o votacion (uno en cada votación)
                "total_opciones": sum(len(v.opciones.all()) for v in c.votaciones.all()),
                "votaciones": [votacion_json(request, v) for v in c.votaciones.all()],
            }
            for c in lista
        ],
    }
    # ensure_ascii=False conserva las tildes y la ñ; indent hace legible el JSON en el navegador.
    return JsonResponse(datos, json_dumps_params={"ensure_ascii": False, "indent": 2})
