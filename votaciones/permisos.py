"""
Roles de la administración (entrega final).

`migrate` crea o actualiza el grupo «Administración del Festival». A un usuario del equipo
de la Fundación se le marca «Es staff» y se le agrega a este grupo: puede configurar una
edición completa sin tocar el código, pero los votos solo los consulta. Los votantes no
tienen acceso a la administración, y solo el superusuario gestiona usuarios y grupos.
"""
GRUPO_ADMINISTRACION = "Administración del Festival"

# (modelo, acciones permitidas) de la app votaciones
PERMISOS_GRUPO = {
    "edicion": ("add", "change", "delete", "view"),
    "categoria": ("add", "change", "delete", "view"),
    "votacion": ("add", "change", "delete", "view"),
    "opcion": ("add", "change", "delete", "view"),
    "voto": ("view",),
}


def crear_grupo_administracion(sender=None, using="default", **kwargs):
    """Se ejecuta después de cada `migrate` (señal post_migrate). Es idempotente."""
    from django.contrib.auth.models import Group, Permission

    grupo, _ = Group.objects.using(using).get_or_create(name=GRUPO_ADMINISTRACION)
    codenames = [f"{accion}_{modelo}" for modelo, acciones in PERMISOS_GRUPO.items() for accion in acciones]
    permisos = Permission.objects.using(using).filter(content_type__app_label="votaciones", codename__in=codenames)
    grupo.permissions.set(permisos)
