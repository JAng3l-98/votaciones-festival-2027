"""
Formularios de la app cuentas: registro de usuarios e inicio de sesión.

Se basan en los formularios que ya trae Django, que validan la contraseña
(longitud, que no sea común ni solo números) y la guardan cifrada.
"""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils import timezone

Usuario = get_user_model()


def aplicar_estilos(formulario):
    """Agrega las clases de Bootstrap a cada campo para que se vea como el prototipo."""
    for campo in formulario.fields.values():
        if isinstance(campo.widget, forms.CheckboxInput):
            campo.widget.attrs["class"] = "form-check-input"
        else:
            campo.widget.attrs["class"] = "form-control"


class RegistroForm(UserCreationForm):
    """Crea una cuenta con nombre, apellidos, correo, contraseña y la autorización de datos."""

    acepta_tratamiento_datos = forms.BooleanField(
        label="Autorizo el tratamiento de mis datos personales según la política de la Fundación (Ley 1581 de 2012).",
        error_messages={"required": "Debes autorizar el tratamiento de tus datos para crear la cuenta."},
    )

    class Meta:
        model = Usuario
        fields = ("first_name", "last_name", "email")
        labels = {"first_name": "Nombre", "last_name": "Apellidos", "email": "Correo electrónico"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre in ("first_name", "last_name", "email"):
            self.fields[nombre].required = True
        self.fields["email"].widget.attrs["placeholder"] = "nombre@correo.com"
        self.fields["password1"].help_text = "Mínimo 8 caracteres. No uses solo números ni una contraseña común."
        aplicar_estilos(self)

    def clean_email(self):
        correo = self.cleaned_data["email"].strip().lower()
        if Usuario.objects.filter(email__iexact=correo).exists():
            raise forms.ValidationError("Ya existe una cuenta con este correo. Ingresa con él o usa otro.")
        return correo

    def save(self, commit=True):
        usuario = super().save(commit=False)
        usuario.username = usuario.email          # Django exige un nombre de usuario: se usa el correo
        usuario.acepta_tratamiento_datos = True
        usuario.fecha_aceptacion_datos = timezone.now()
        if commit:
            usuario.save()
        return usuario


class IngresoForm(AuthenticationForm):
    """El formulario de inicio de sesión de Django, con los estilos del sitio."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs["placeholder"] = "nombre@correo.com"
        aplicar_estilos(self)
