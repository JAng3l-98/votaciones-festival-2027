"""
Usuario del sistema. Se usa el modelo de usuarios de Django (AbstractUser), que ya trae
contraseñas cifradas, permisos y grupos, y se ajusta para ingresar con el correo.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    email = models.EmailField("correo electrónico", unique=True)
    acepta_tratamiento_datos = models.BooleanField(
        "acepta el tratamiento de datos personales", default=False,
        help_text="Autorización según la Ley 1581 de 2012.")
    fecha_aceptacion_datos = models.DateTimeField("fecha de la autorización", null=True, blank=True)

    # Se ingresa con el correo; el nombre de usuario se sigue guardando por compatibilidad.
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"

    def __str__(self):
        return self.get_full_name() or self.email
