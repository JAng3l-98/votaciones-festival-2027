from django.contrib import admin

from .models import Categoria, Edicion, Opcion, Votacion


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
    list_display = ("nombre", "edicion", "orden", "visible")
    list_filter = ("visible", "edicion")
    search_fields = ("nombre", "slug", "descripcion")
    ordering = ("edicion", "orden", "nombre")
    list_editable = ("orden", "visible")          # agregado: se cambian desde la lista
    prepopulated_fields = {"slug": ("nombre",)}   # agregado: el identificador se escribe solo


class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 3
    fields = ("nombre", "descripcion", "orden", "activa")


@admin.register(Votacion)
class VotacionAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "categoria",
        "estado",                                 # agregado: columna calculada (ver abajo)
        "fecha_apertura",
        "fecha_cierre",
        "visible",
        "es_prueba",
    )
    list_filter = ("visible", "es_prueba", "publicacion_resultados")
    search_fields = ("nombre", "slug", "descripcion")
    ordering = ("categoria", "orden", "fecha_apertura")
    inlines = [OpcionInline]
    prepopulated_fields = {"slug": ("nombre",)}   # agregado: el identificador se escribe solo

    # agregado: el formulario en tres bloques; el último reúne las reglas que la Fundación debe aprobar
    fieldsets = (
        ("Datos de la votación", {"fields": ("categoria", "nombre", "slug", "descripcion", "imagen", "orden", "visible")}),
        ("Fechas", {"fields": ("fecha_apertura", "fecha_cierre")}),
        ("Reglas configurables (pendientes de validación con la Fundación)", {
            "fields": ("votos_por_usuario", "publicacion_resultados", "es_prueba"),
        }),
    )

    # agregado: muestra Abierta, Próximamente o Cerrada según las fechas
    @admin.display(description="estado")
    def estado(self, votacion):
        return votacion.get_estado_display()


@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "votacion", "orden", "activa")
    list_filter = ("activa",)
    search_fields = ("nombre", "descripcion", "votacion__nombre")
    ordering = ("votacion", "orden", "nombre")


admin.site.site_header = "Administración · Votaciones del Festival"
admin.site.site_title = "Votaciones del Festival"
admin.site.index_title = "Ediciones, categorías, votaciones y opciones"
