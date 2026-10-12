from django.contrib import admin

from .models import Equipo, Jugador, Liga, Partido


@admin.register(Liga)
class LigaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "pais", "temporada")
    list_filter = ("pais", "temporada")
    search_fields = ("nombre", "pais")


@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ciudad", "liga")
    list_filter = ("liga",)
    search_fields = ("nombre", "ciudad")


@admin.register(Jugador)
class JugadorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "numero", "posicion", "equipo")
    list_filter = ("posicion", "equipo__liga", "equipo")
    search_fields = ("nombre", "equipo__nombre")


@admin.register(Partido)
class PartidoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "liga", "fecha", "estadio", "estado")
    list_filter = ("estado", "liga")
    search_fields = ("local__nombre", "visita__nombre", "estadio")
    date_hierarchy = "fecha"
