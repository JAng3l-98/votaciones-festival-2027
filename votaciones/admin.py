"""
Administración del sistema en Django Admin.

Permisos (entrega final):
  · Votantes: usuarios sin acceso a la administración (is_staff = False).
  · Grupo «Administración del Festival»: gestiona ediciones, categorías, votaciones y opciones,
    y solo consulta los votos. Lo crea `migrate` (ver permisos.py).
  · Superusuario: además gestiona usuarios y grupos.
Nadie puede crear, modificar ni borrar votos desde aquí: se registran solo desde el sitio,
con todas sus validaciones. Tampoco se pueden hacer cambios que dejarían votos ya
registrados en el lugar equivocado (mover una opción, una votación o una categoría).
"""
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from django.utils.timezone import localtime

from .ediciones import duplicar_edicion
from .models import Categoria, Edicion, Opcion, Votacion, Voto


def solo_lectura_si_tiene_votos(obj, campos):
    """Campos que se vuelven de solo lectura cuando el objeto ya tiene votos."""
    return campos if obj is not None and obj.pk and obj.votos.exists() else ()


@admin.register(Edicion)
class EdicionAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "anio",
        "numero",
        "activa",
        "fecha_inicio",
        "fecha_fin",
        "total_categorias",
    )
    list_filter = ("activa", "anio")
    search_fields = ("nombre", "anio", "descripcion")
    ordering = ("-anio",)
    actions = ["duplicar_para_el_anio_siguiente", "marcar_como_activa"]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(categorias_registradas=Count("categorias"))

    @admin.display(description="categorías", ordering="categorias_registradas")
    def total_categorias(self, edicion):
        return edicion.categorias_registradas

    @admin.action(description="Duplicar para el año siguiente (categorías, votaciones y opciones)",
                  permissions=["add"])
    def duplicar_para_el_anio_siguiente(self, request, queryset):
        for edicion in queryset:
            try:
                nueva, totales = duplicar_edicion(edicion)
            except ValidationError as error:
                self.message_user(request, " ".join(error.messages), messages.ERROR)
                continue
            self.message_user(
                request,
                f"Se creó «{nueva}» con {totales['categorias']} categorías, {totales['votaciones']} votaciones "
                f"y {totales['opciones']} opciones, con las fechas corridas un año. Quedó inactiva: "
                "revisa sus participantes y fechas, y actívala cuando esté lista.",
                messages.SUCCESS,
            )

    @admin.action(description="Marcar como la edición activa (la que ve el público)", permissions=["change"])
    def marcar_como_activa(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "Selecciona una sola edición para activarla.", messages.WARNING)
            return
        edicion = queryset.get()
        edicion.activa = True
        edicion.save()   # save() desactiva las demás
        self.message_user(request, f"«{edicion}» es ahora la edición activa del sitio.", messages.SUCCESS)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "edicion", "regla_voto", "orden", "visible")
    list_filter = ("visible", "edicion", "regla_voto")
    search_fields = ("nombre", "slug", "descripcion")
    ordering = ("edicion", "orden", "nombre")
    list_editable = ("orden", "visible")
    prepopulated_fields = {"slug": ("nombre",)}

    def get_readonly_fields(self, request, obj=None):
        # Con votos, la categoría no puede pasar a otra edición. Su regla tampoco cambia: si se
        # intenta, el modelo lo rechaza con un mensaje (Categoria.clean).
        return super().get_readonly_fields(request, obj) + solo_lectura_si_tiene_votos(obj, ("edicion",))


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
        "cierra",
        "total_votos",
        "ver_resultados",
        "visible",
        "es_prueba",
    )
    list_filter = ("visible", "es_prueba", "publicacion_resultados", "audiencia_resultados", "categoria__edicion")
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
        ("Resultados", {
            "fields": ("publicacion_resultados", "audiencia_resultados"),
            "description": "Cuándo se publican los resultados y a quiénes se muestran. "
                           "La administración los puede consultar siempre.",
        }),
        ("Votación de prueba", {
            "fields": ("es_prueba",),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(votos_recibidos=Count("votos"))

    def get_readonly_fields(self, request, obj=None):
        # Con votos, la votación no puede pasar a otra categoría.
        return super().get_readonly_fields(request, obj) + solo_lectura_si_tiene_votos(obj, ("categoria",))

    @admin.display(description="estado")
    def estado(self, votacion):
        return votacion.get_estado_display()

    @admin.display(description="cierra", ordering="fecha_cierre")
    def cierra(self, votacion):
        return localtime(votacion.fecha_cierre).strftime("%d/%m/%Y %H:%M")

    @admin.display(description="votos", ordering="votos_recibidos")
    def total_votos(self, votacion):
        return votacion.votos_recibidos

    @admin.display(description="resultados")
    def ver_resultados(self, votacion):
        return format_html('<a href="{}">Ver</a>', reverse("votaciones:resultados_votacion", args=[votacion.pk]))


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

    def get_readonly_fields(self, request, obj=None):
        # Con votos, la opción no puede pasar a otra votación.
        return super().get_readonly_fields(request, obj) + solo_lectura_si_tiene_votos(obj, ("votacion",))

    @admin.display(description="votos", ordering="votos_recibidos")
    def total_votos(self, opcion):
        return opcion.votos_recibidos


@admin.register(Voto)
class VotoAdmin(admin.ModelAdmin):
    """
    Consulta administrativa de los votos. Es solo de lectura para todos, también para el
    superusuario: los votos se crean únicamente desde el sitio, con todas sus validaciones,
    y no se pueden editar ni borrar desde aquí. El historial de la administración queda en
    el registro de Django (LogEntry).
    """

    list_display = ("fecha", "correo", "votacion", "opcion", "comprobante")
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
    actions = None   # sin acciones masivas, como «Eliminar seleccionados»
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
        return False


admin.site.site_header = "Administración · Votaciones del Festival"
admin.site.site_title = "Votaciones del Festival"
admin.site.index_title = "Ediciones, categorías, votaciones y opciones"
