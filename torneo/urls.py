from django.urls import path

from . import views as v

urlpatterns = [
    # Partidos (página de inicio)
    path("", v.PartidoListView.as_view(), name="partido_list"),
    path("partidos/nuevo/", v.PartidoCreateView.as_view(), name="partido_create"),
    path("partidos/<int:pk>/", v.PartidoDetailView.as_view(), name="partido_detail"),
    path("partidos/<int:pk>/editar/", v.PartidoUpdateView.as_view(), name="partido_update"),
    path("partidos/<int:pk>/borrar/", v.PartidoDeleteView.as_view(), name="partido_delete"),
    path("partidos/<int:pk>/marcador/", v.MarcadorUpdateView.as_view(), name="partido_marcador"),
    # Ligas
    path("ligas/", v.LigaListView.as_view(), name="liga_list"),
    path("ligas/nueva/", v.LigaCreateView.as_view(), name="liga_create"),
    path("ligas/<int:pk>/", v.LigaDetailView.as_view(), name="liga_detail"),
    path("ligas/<int:pk>/editar/", v.LigaUpdateView.as_view(), name="liga_update"),
    path("ligas/<int:pk>/borrar/", v.LigaDeleteView.as_view(), name="liga_delete"),
    # Equipos
    path("equipos/", v.EquipoListView.as_view(), name="equipo_list"),
    path("equipos/nuevo/", v.EquipoCreateView.as_view(), name="equipo_create"),
    path("equipos/<int:pk>/", v.EquipoDetailView.as_view(), name="equipo_detail"),
    path("equipos/<int:pk>/editar/", v.EquipoUpdateView.as_view(), name="equipo_update"),
    path("equipos/<int:pk>/borrar/", v.EquipoDeleteView.as_view(), name="equipo_delete"),
    # Jugadores
    path("jugadores/", v.JugadorListView.as_view(), name="jugador_list"),
    path("jugadores/nuevo/", v.JugadorCreateView.as_view(), name="jugador_create"),
    path("jugadores/<int:pk>/", v.JugadorDetailView.as_view(), name="jugador_detail"),
    path("jugadores/<int:pk>/editar/", v.JugadorUpdateView.as_view(), name="jugador_update"),
    path("jugadores/<int:pk>/borrar/", v.JugadorDeleteView.as_view(), name="jugador_delete"),
]
