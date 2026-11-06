from django.contrib import admin
from django.db.models import Count

from .models import Categoria, Edicion, Opcion, Votacion, Voto


@admin.register(Edicion)
class EdicionAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "anio",
        "numero",
        "activa",
        "fecha_inicio",
        "fecha_fin",
    )
    list_filter = ("activa", "anio")
    search_fields = ("nombre", "anio", "descripcion")
    ordering = ("-anio",)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "edicion", "regla_voto", "orden", "visible")
    list_filter = ("visible", "edicion", "regla_voto")
    search_fields = ("nombre", "slug", "descripcion")
    ordering = ("edicion", "orden", "nombre")
    list_editable = ("orden", "visible")
    prepopulated_fields = {"slug": ("nombre",)}


class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 3
    fields = ("nombre", "descripcion", "orden", "activa")


@admin.register(Votacion)
class VotacionAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "categoria",
        "estado",
        "fecha_apertura",
        "fecha_cierre",
        "visible",
        "es_prueba",
    )
    list_filter = ("visible", "es_prueba", "publicacion_resultados")
    search_fields = ("nombre", "slug", "descripcion")
    ordering = ("categoria", "orden", "fecha_apertura")
    inlines = [OpcionInline]
    prepopulated_fields = {"slug": ("nombre",)}

    fieldsets = (
        ("Datos de la votación", {
            "fields": (
                "categoria", "nombre", "slug", "descripcion",
                "imagen", "orden", "visible"
            )
        }),
        ("Fechas", {
            "fields": ("fecha_apertura", "fecha_cierre")
        }),
        ("Reglas configurables (pendientes de validación con la Fundación)", {
            "fields": ("publicacion_resultados", "es_prueba"),
        }),
    )

    @admin.display(description="estado")
    def estado(self, votacion):
        return votacion.get_estado_display()


@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "votacion", "orden", "activa", "total_votos")
    list_filter = ("activa", "votacion__categoria")
    search_fields = ("nombre", "descripcion", "votacion__nombre")
    ordering = ("votacion", "orden", "nombre")

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            votos_recibidos=Count("votos")
        )

    @admin.display(description="votos", ordering="votos_recibidos")
    def total_votos(self, opcion):
        return opcion.votos_recibidos


@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    """
    Consulta administrativa de los votos. Es solo de lectura: los votos se crean
    únicamente desde el sitio, con todas sus validaciones, y no se pueden editar
    desde aquí.
    """

    list_display = (
        "fecha", "usuario", "correo", "categoria",
        "votacion", "opcion", "comprobante"
    )
    list_filter = ("edicion", "categoria", "votacion")
    search_fields = (
        "usuario__email",
        "usuario__first_name",
        "usuario__last_name",
        "opcion__nombre",
        "comprobante",
    )
    list_select_related = (
        "usuario", "edicion", "categoria", "votacion", "opcion"
    )
    ordering = ("-fecha",)
    list_per_page = 50
    fields = (
        "comprobante", "fecha", "usuario", "edicion",
        "categoria", "votacion", "opcion"
    )
    readonly_fields = fields

    @admin.display(description="correo", ordering="usuario__email")
    def correo(self, voto):
        return voto.usuario.email

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


admin.site.site_header = "Administración · Votaciones del Festival"
admin.site.site_title = "Votaciones del Festival"
admin.site.index_title = "Ediciones, categorías, votaciones y opciones"
