from django.urls import path
from rest_framework.routers import DefaultRouter

from . import api_views as v

router = DefaultRouter()
router.register("ligas", v.LigaViewSet, basename="liga")
router.register("equipos", v.EquipoViewSet, basename="equipo")
router.register("jugadores", v.JugadorViewSet, basename="jugador")
router.register("partidos", v.PartidoViewSet, basename="partido")

urlpatterns = [
    path("token/", v.LoginView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", v.RefreshView.as_view(), name="token_refresh"),
    path("me/", v.MeView.as_view(), name="me"),
] + router.urls
