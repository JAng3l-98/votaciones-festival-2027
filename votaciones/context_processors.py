from .models import Edicion


def edicion_activa(request):
    """Pone la edición activa a disposición de todas las plantillas (por ejemplo, en el encabezado)."""
    return {"edicion_activa": Edicion.objects.activa()}
