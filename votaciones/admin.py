from django.contrib import admin

from .models import Categoria, Edicion, Opcion, Votacion

# Registro básico para administrar los datos desde Django Admin.
# La tarea de administración amplía este archivo con columnas, filtros, búsqueda
# y la edición de las opciones dentro de cada votación.
admin.site.register(Edicion)
admin.site.register(Categoria)
admin.site.register(Votacion)
admin.site.register(Opcion)

admin.site.site_header = "Administración · Votaciones del Festival"
admin.site.site_title = "Votaciones del Festival"
admin.site.index_title = "Ediciones, categorías, votaciones y opciones"
