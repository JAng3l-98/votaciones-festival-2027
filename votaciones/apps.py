from django.apps import AppConfig
from django.db.models.signals import post_migrate


class VotacionesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "votaciones"
    verbose_name = "Votaciones del Festival"

    def ready(self):
        # Después de cada migrate se crea o actualiza el grupo «Administración del Festival».
        from .permisos import crear_grupo_administracion
        post_migrate.connect(crear_grupo_administracion, sender=self, dispatch_uid="grupo_administracion_festival")
