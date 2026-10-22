from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from .models import Usuario


class UsuarioCreacionAdminForm(AdminUserCreationForm):
    class Meta(AdminUserCreationForm.Meta):
        model = Usuario
        fields = ("email", "username", "first_name", "last_name")


class UsuarioCambioAdminForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = "__all__"


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    form = UsuarioCambioAdminForm
    add_form = UsuarioCreacionAdminForm
    list_display = ("email", "first_name", "last_name", "is_staff", "acepta_tratamiento_datos")
    search_fields = ("email", "first_name", "last_name", "username")
    ordering = ("email",)
    fieldsets = UserAdmin.fieldsets + (
        ("Tratamiento de datos personales", {"fields": ("acepta_tratamiento_datos", "fecha_aceptacion_datos")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",),
                "fields": ("email", "username", "first_name", "last_name", "usable_password", "password1", "password2")}),
    )
