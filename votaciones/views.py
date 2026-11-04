"""
Vistas públicas (la «V» del patrón MVT). Cada vista consulta MySQL a través de los
modelos y entrega los datos a una plantilla. Solo se muestra la edición activa y
lo que el administrador dejó visible.

Entrega 3: el proceso de votación (elegir → confirmar → registrar) usa solo POST con
token CSRF y exige sesión iniciada. Las reglas del voto están en servicios.py.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import Categoria, Edicion, Votacion, Voto
from .servicios import VotoRechazado, registrar_voto, validar_voto, voto_que_bloquea


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
    # Si un voto del usuario ya le impide votar aquí (según la regla de la categoría),
    # la página lo muestra en lugar del formulario.
    voto_usuario = voto_que_bloquea(request.user, votacion)
    return render(request, "votaciones/detalle.html", {
        "votacion": votacion, "opciones": opciones, "voto_usuario": voto_usuario,
        "puede_votar": votacion.estado == Votacion.Estado.ABIERTA and voto_usuario is None,
    })


# ---------------------------------------------------------------- Proceso de votación (Entrega 3)
def votacion_o_404(pk):
    return get_object_or_404(Votacion.objects.select_related("categoria__edicion"), pk=pk)


def volver(votacion):
    """A dónde regresa el usuario cuando el voto se rechaza."""
    if votacion.visible and votacion.categoria.visible:
        return redirect(votacion)
    return redirect("votaciones:lista")


@require_POST
def confirmar(request, pk):
    """Paso 2: muestra la opción elegida para que el usuario la confirme. Todavía no guarda nada."""
    votacion = votacion_o_404(pk)
    if not request.user.is_authenticated:
        return redirect_to_login(votacion.get_absolute_url())   # después de ingresar vuelve a la votación
    try:
        opcion = validar_voto(request.user, votacion, request.POST.get("opcion"))
    except VotoRechazado as error:
        messages.error(request, str(error))
        return volver(votacion)
    return render(request, "votaciones/confirmar.html", {"votacion": votacion, "opcion": opcion})


@require_POST
def votar(request, pk):
    """Paso 3: valida de nuevo en el servidor y guarda el voto en MySQL."""
    votacion = votacion_o_404(pk)
    if not request.user.is_authenticated:
        return redirect_to_login(votacion.get_absolute_url())
    try:
        voto = registrar_voto(request.user, votacion, request.POST.get("opcion"))
    except VotoRechazado as error:
        messages.error(request, str(error))
        return volver(votacion)
    # Se redirige (patrón POST/redirección/GET): si el usuario recarga la página, no reenvía el voto.
    return redirect("votaciones:voto_registrado", comprobante=voto.comprobante)


@login_required
def voto_registrado(request, comprobante):
    """Paso 4: el comprobante. Cada usuario solo puede ver los suyos."""
    voto = get_object_or_404(Voto.objects.select_related("opcion", "votacion", "categoria", "edicion"),
                             comprobante=comprobante, usuario=request.user)
    return render(request, "votaciones/voto_registrado.html", {"voto": voto})
