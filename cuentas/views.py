from django.shortcuts import render


# Página temporal. La tarea de autenticación la reemplaza por el formulario de registro.
def registro(request):
    return render(request, "en_construccion.html", {"titulo": "Crear cuenta"})
