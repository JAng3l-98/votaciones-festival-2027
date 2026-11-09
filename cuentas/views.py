from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from votaciones.models import Categoria, Edicion, Votacion
from votaciones.servicios import voto_que_bloquea

from .forms import RegistroForm


def registro(request):
    """Muestra el formulario de registro y, si los datos son válidos, crea la cuenta."""
    if request.user.is_authenticated:
        return redirect("votaciones:inicio")

    if request.method == "POST":
        formulario = RegistroForm(request.POST)
        if formulario.is_valid():
            usuario = formulario.save()
            messages.success(request, f"Listo, {usuario.first_name}: tu cuenta quedó creada. Ingresa con tu correo y tu contraseña.")
            return redirect("cuentas:login")
    else:
        formulario = RegistroForm()

    return render(request, "cuentas/registro.html", {"form": formulario})


@login_required
def mis_votos(request):
    """Participación del usuario: los votos que ha emitido en la edición activa y las categorías donde aún no vota."""
    edicion = Edicion.objects.activa()
    votos, pendientes, total_categorias = [], [], 0
    if edicion:
        # Solo se consultan los votos del usuario que inició sesión (request.user): nadie ve los de otro.
        votos = list(request.user.votos.filter(edicion=edicion)
                     .select_related("categoria", "votacion", "opcion"))
        categorias = list(Categoria.objects.filter(edicion=edicion, visible=True))
        votadas = {voto.categoria_id for voto in votos}
        # Categorías con al menos una votación abierta en la que todavía puede votar,
        # según la regla de cada categoría (la misma función que usa el registro del voto).
        abiertas = (Votacion.objects.de_edicion(edicion).visibles().abiertas()
                    .select_related("categoria").order_by("categoria__orden", "orden"))
        for votacion in abiertas:
            if voto_que_bloquea(request.user, votacion) is None and votacion.categoria not in pendientes:
                pendientes.append(votacion.categoria)
        total_categorias = len(categorias)
    contexto = {"edicion": edicion, "votos": votos, "pendientes": pendientes,
                "total_categorias": total_categorias,
                "categorias_votadas": len(votadas)}
    return render(request, "cuentas/mis_votos.html", contexto)
