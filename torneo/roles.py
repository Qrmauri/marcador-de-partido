"""Roles del sitio y la API.

- Público (sin sesión): solo mira.
- "planillero" (grupo): puede actualizar SOLO goles_local, goles_visita y estado.
- "administrador" (grupo o superusuario): CRUD completo.
"""
from django.contrib.auth.mixins import UserPassesTestMixin

ROL_ADMIN = "administrador"
ROL_PLANILLERO = "planillero"
ROL_LECTOR = "lector"


def _en_grupo(user, nombre):
    return bool(user and user.is_authenticated and user.groups.filter(name__iexact=nombre).exists())


def es_administrador(user):
    return bool(user and user.is_authenticated and (user.is_superuser or _en_grupo(user, ROL_ADMIN)))


def es_planillero(user):
    return _en_grupo(user, ROL_PLANILLERO)


def rol_de(user):
    if es_administrador(user):
        return ROL_ADMIN
    if es_planillero(user):
        return ROL_PLANILLERO
    return ROL_LECTOR


def contexto_roles(request):
    """Context processor: expone el rol a todas las plantillas (navbar, botones)."""
    user = request.user
    return {
        "rol": rol_de(user) if user.is_authenticated else None,
        "es_admin": es_administrador(user),
        "es_planillero": es_planillero(user),
    }


class AdministradorRequeridoMixin(UserPassesTestMixin):
    """Sin sesión -> redirige al login. Con sesión pero sin rol -> 403."""

    def test_func(self):
        return es_administrador(self.request.user)


class PlanilleroOAdminRequeridoMixin(UserPassesTestMixin):
    def test_func(self):
        return es_administrador(self.request.user) or es_planillero(self.request.user)
