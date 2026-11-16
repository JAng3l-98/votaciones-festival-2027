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
    list_display = ("email", "first_name", "last_name", "rol", "is_active", "acepta_tratamiento_datos")
    list_filter = ("is_staff", "is_superuser", "groups", "is_active")
    search_fields = ("email", "first_name", "last_name", "username")
    ordering = ("email",)
    fieldsets = UserAdmin.fieldsets + (
        ("Tratamiento de datos personales", {"fields": ("acepta_tratamiento_datos", "fecha_aceptacion_datos")}),
    )
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("groups")

    @admin.display(description="rol")
    def rol(self, usuario):
        """Permisos diferenciados: votante, equipo de la Fundación (grupo) o superusuario."""
        if usuario.is_superuser:
            return "Superusuario"
        if usuario.is_staff:
            grupos = ", ".join(g.name for g in usuario.groups.all())
            return grupos or "Equipo (sin grupo)"
        return "Votante"

    add_fieldsets = (
        (None, {"classes": ("wide",),
                "fields": ("email", "username", "first_name", "last_name", "usable_password", "password1", "password2")}),
    )
