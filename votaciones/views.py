"""
Vistas públicas (la «V» del patrón MVT). Cada vista consulta MySQL a través de los
modelos y entrega los datos a una plantilla. Solo se muestra la edición activa y
lo que el administrador dejó visible.

Entrega 3: el proceso de votación (elegir → confirmar → registrar) usa solo POST con
token CSRF y exige sesión iniciada. Las reglas del voto están en servicios.py.

Entrega final: resultados de cada votación, con las reglas de cuándo y a quiénes se
publican (resultados.py), y su descarga en CSV para la administración.
"""
import csv

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Categoria, Edicion, Votacion, Voto
from .resultados import acceso_resultados, contar, es_administracion, regla_publicacion
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
        "acceso_resultados": acceso_resultados(request.user, votacion),
        "regla_resultados": regla_publicacion(votacion),
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
    return render(request, "votaciones/voto_registrado.html", {
        "voto": voto,
        "regla_resultados": regla_publicacion(voto.votacion),
        "acceso_resultados": acceso_resultados(request.user, voto.votacion),
    })


# ---------------------------------------------------------------- Resultados (entrega final)
def votacion_para_resultados(request, pk):
    """El público solo ve votaciones visibles; la administración puede revisar cualquiera."""
    votaciones = Votacion.objects.select_related("categoria__edicion")
    if not es_administracion(request.user):
        votaciones = votaciones.visibles()
    return get_object_or_404(votaciones, pk=pk)


def resultados_lista(request):
    """Todas las votaciones de la edición activa, con sus resultados o la fecha en que se publican."""
    edicion = Edicion.objects.activa()
    grupos = []
    if edicion:
        votaciones = (Votacion.objects.de_edicion(edicion).visibles()
                      .select_related("categoria").annotate(total_votos=Count("votos"))
                      .order_by("categoria__orden", "categoria__nombre", "orden", "fecha_apertura"))
        for votacion in votaciones:
            fila = {"votacion": votacion, "acceso": acceso_resultados(request.user, votacion)}
            if grupos and grupos[-1]["categoria"] == votacion.categoria:
                grupos[-1]["filas"].append(fila)
            else:
                grupos.append({"categoria": votacion.categoria, "filas": [fila]})
    return render(request, "votaciones/resultados_lista.html", {"edicion": edicion, "grupos": grupos})


def resultados(request, pk):
    """Resultados de una votación, contados en MySQL, si las reglas de publicación lo permiten."""
    votacion = votacion_para_resultados(request, pk)
    acceso = acceso_resultados(request.user, votacion)
    contexto = {"votacion": votacion, "acceso": acceso, "regla_resultados": regla_publicacion(votacion),
                "consultado": timezone.now()}
    if acceso.permitido:
        contexto["conteo"] = contar(votacion)
    return render(request, "votaciones/resultados.html", contexto)


@staff_member_required
def resultados_csv(request, pk):
    """Descarga los resultados en CSV (solo administración), para archivarlos o revisarlos en una hoja."""
    votacion = get_object_or_404(Votacion.objects.select_related("categoria__edicion"), pk=pk)
    conteo = contar(votacion)
    respuesta = HttpResponse(content_type="text/csv; charset=utf-8")
    respuesta["Content-Disposition"] = f'attachment; filename="resultados-{votacion.pk}-{votacion.slug}.csv"'
    respuesta.write("\ufeff")   # para que Excel reconozca las tildes
    # Punto y coma y coma decimal: así lo abre Excel configurado en español (Colombia).
    escritor = csv.writer(respuesta, delimiter=";")
    escritor.writerow(["Edición", "Categoría", "Votación", "Opción", "Votos", "Porcentaje"])
    for fila in conteo.filas:
        escritor.writerow([votacion.categoria.edicion.anio, votacion.categoria.nombre, votacion.nombre,
                           fila.nombre, fila.votos, f"{fila.porcentaje:.1f}".replace(".", ",")])
    escritor.writerow([votacion.categoria.edicion.anio, votacion.categoria.nombre, votacion.nombre,
                       "Total", conteo.total, "100,0" if conteo.total else "0,0"])
    return respuesta
