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


class OpcionInline(admin.TabularInline):
    model = Opcion
    extra = 3
    fields = ("nombre", "descripcion", "orden", "activa")


@admin.register(Votacion)
class VotacionAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "categoria",
        "fecha_apertura",
        "fecha_cierre",
        "visible",
        "es_prueba",
    )
    list_filter = ("visible", "es_prueba", "publicacion_resultados")
    search_fields = ("nombre", "slug", "descripcion")
    ordering = ("categoria", "orden", "fecha_apertura")
    inlines = [OpcionInline]


@admin.register(Opcion)
class OpcionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "votacion", "orden", "activa")
    list_filter = ("activa",)
    search_fields = ("nombre", "descripcion", "votacion__nombre")
    ordering = ("votacion", "orden", "nombre")


admin.site.site_header = "Administración · Votaciones del Festival"
admin.site.site_title = "Votaciones del Festival"
admin.site.index_title = "Ediciones, categorías, votaciones y opciones"
