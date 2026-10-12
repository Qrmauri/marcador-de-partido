"""API REST: ViewSets + DefaultRouter, /token/, /me/ y tabla de posiciones."""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Equipo, Jugador, Liga, Partido
from .permissions import AdminOEscrituraRestringida, PermisoPartido
from .roles import rol_de
from .serializers import (
    EquipoSerializer, JugadorSerializer, LigaSerializer, PartidoSerializer,
)


def _entero(request, nombre):
    """Lee un filtro entero del query string; si no es entero -> 400."""
    valor = request.query_params.get(nombre)
    if valor in (None, ""):
        return None
    try:
        return int(valor)
    except ValueError:
        raise ValidationError({nombre: "Debe ser un número entero."})


# ------------------------------------------------------------------ JWT
class LoginView(TokenObtainPairView):
    throttle_scope = "login"


class RefreshView(TokenRefreshView):
    throttle_scope = "login"


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        return Response({"id": u.id, "username": u.username, "rol": rol_de(u)})


# ----------------------------------------------------------- ViewSets
class LigaViewSet(viewsets.ModelViewSet):
    queryset = Liga.objects.all()
    serializer_class = LigaSerializer
    permission_classes = [AdminOEscrituraRestringida]

    @action(detail=True, methods=["get"], url_path="tabla", pagination_class=None)
    def tabla(self, request, pk=None):
        """Posiciones: solo partidos FINALIZADOS. 3 pts victoria, 1 empate."""
        liga = self.get_object()
        filas = {
            e.id: {"equipo_id": e.id, "equipo": e.nombre, "pj": 0, "pg": 0, "pe": 0,
                   "pp": 0, "gf": 0, "gc": 0, "dg": 0, "pts": 0}
            for e in liga.equipos.all()
        }
        finalizados = liga.partidos.filter(estado=Partido.Estado.FINALIZADO)
        for p in finalizados.select_related("local", "visita"):
            for equipo, gf, gc in ((p.local, p.goles_local, p.goles_visita),
                                   (p.visita, p.goles_visita, p.goles_local)):
                f = filas.setdefault(equipo.id, {
                    "equipo_id": equipo.id, "equipo": equipo.nombre, "pj": 0, "pg": 0,
                    "pe": 0, "pp": 0, "gf": 0, "gc": 0, "dg": 0, "pts": 0})
                f["pj"] += 1
                f["gf"] += gf
                f["gc"] += gc
                if gf > gc:
                    f["pg"] += 1
                    f["pts"] += 3
                elif gf == gc:
                    f["pe"] += 1
                    f["pts"] += 1
                else:
                    f["pp"] += 1
        for f in filas.values():
            f["dg"] = f["gf"] - f["gc"]
        orden = sorted(filas.values(), key=lambda f: (-f["pts"], -f["dg"], -f["gf"], f["equipo"]))
        return Response(orden)


class EquipoViewSet(viewsets.ModelViewSet):
    serializer_class = EquipoSerializer
    permission_classes = [AdminOEscrituraRestringida]

    def get_queryset(self):
        qs = Equipo.objects.select_related("liga")
        liga = _entero(self.request, "liga")
        return qs.filter(liga_id=liga) if liga is not None else qs


class JugadorViewSet(viewsets.ModelViewSet):
    serializer_class = JugadorSerializer
    permission_classes = [AdminOEscrituraRestringida]

    def get_queryset(self):
        qs = Jugador.objects.select_related("equipo")
        equipo = _entero(self.request, "equipo")
        return qs.filter(equipo_id=equipo) if equipo is not None else qs


class PartidoViewSet(viewsets.ModelViewSet):
    serializer_class = PartidoSerializer
    permission_classes = [PermisoPartido]

    def get_queryset(self):
        qs = Partido.objects.select_related("liga", "local", "visita")
        liga = _entero(self.request, "liga")
        if liga is not None:
            qs = qs.filter(liga_id=liga)
        estado = self.request.query_params.get("estado")
        if estado:
            if estado not in Partido.Estado.values:
                raise ValidationError({"estado": f"Valores válidos: {', '.join(Partido.Estado.values)}."})
            qs = qs.filter(estado=estado)
        return qs
