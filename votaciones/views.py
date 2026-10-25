"""
Vistas públicas (la «V» del patrón MVT). Cada vista consulta MySQL a través de los
modelos y entrega los datos a una plantilla. Solo se muestra la edición activa y
lo que el administrador dejó visible.
"""
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render

from .models import Categoria, Edicion, Votacion


def inicio(request):
    edicion = Edicion.objects.activa()
    contexto = {"edicion": edicion, "total_categorias": 0, "total_votaciones": 0, "abiertas": []}
    if edicion:
        votaciones = Votacion.objects.de_edicion(edicion).visibles().select_related("categoria")
        contexto["total_categorias"] = edicion.categorias.filter(visible=True).count()
        contexto["total_votaciones"] = votaciones.count()
        contexto["abiertas"] = votaciones.abiertas().order_by("fecha_cierre")[:3]
    return render(request, "votaciones/inicio.html", contexto)


def categorias(request):
    edicion = Edicion.objects.activa()
    lista_categorias = []
    if edicion:
        lista_categorias = (
            Categoria.objects.filter(edicion=edicion, visible=True)
            .annotate(total=Count("votaciones", filter=Q(votaciones__visible=True)))
        )
    return render(request, "votaciones/categorias.html", {"edicion": edicion, "categorias": lista_categorias})


def lista(request):
    edicion = Edicion.objects.activa()
    contexto = {"edicion": edicion, "categorias": [], "categoria_actual": None,
                "abiertas": [], "proximas": [], "cerradas": []}
    if edicion:
        contexto["categorias"] = Categoria.objects.filter(edicion=edicion, visible=True)
        votaciones = Votacion.objects.de_edicion(edicion).visibles().select_related("categoria")

        # Filtro por categoría: /votaciones/?categoria=musica
        slug = request.GET.get("categoria")
        if slug:
            contexto["categoria_actual"] = get_object_or_404(contexto["categorias"], slug=slug)
            votaciones = votaciones.filter(categoria=contexto["categoria_actual"])

        contexto["abiertas"] = votaciones.abiertas().order_by("fecha_cierre")
        contexto["proximas"] = votaciones.proximas().order_by("fecha_apertura")
        contexto["cerradas"] = votaciones.cerradas().order_by("-fecha_cierre")
    return render(request, "votaciones/lista.html", contexto)


def detalle(request, pk):
    votacion = get_object_or_404(Votacion.objects.visibles().select_related("categoria__edicion"), pk=pk)
    opciones = votacion.opciones.filter(activa=True)
    return render(request, "votaciones/detalle.html", {"votacion": votacion, "opciones": opciones})
