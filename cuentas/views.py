from django.contrib import messages
from django.shortcuts import redirect, render

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
