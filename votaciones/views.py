"""
Vistas públicas (la «V» del patrón MVT). Cada vista consulta MySQL a través de los
modelos y entrega los datos a una plantilla.
"""
from django.shortcuts import render

from .models import Edicion, Votacion


def inicio(request):
    edicion = Edicion.objects.activa()
    contexto = {"edicion": edicion, "total_categorias": 0, "total_votaciones": 0}
    if edicion:
        contexto["total_categorias"] = edicion.categorias.filter(visible=True).count()
        contexto["total_votaciones"] = Votacion.objects.de_edicion(edicion).visibles().count()
    return render(request, "votaciones/inicio.html", contexto)


# Las tres vistas siguientes muestran por ahora una página «en construcción».
# La tarea de la interfaz pública las reemplaza por las consultas reales.
def categorias(request):
    return render(request, "en_construccion.html", {"titulo": "Categorías"})


def lista(request):
    return render(request, "en_construccion.html", {"titulo": "Votaciones"})


def detalle(request, pk):
    return render(request, "en_construccion.html", {"titulo": "Detalle de la votación"})
