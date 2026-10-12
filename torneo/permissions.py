"""Permisos propios por rol (BasePermission)."""
from rest_framework.permissions import SAFE_METHODS, BasePermission

from .roles import es_administrador, es_planillero

CAMPOS_PLANILLERO = {"goles_local", "goles_visita", "estado"}


class AdminOEscrituraRestringida(BasePermission):
    """Lectura: todos. Escritura: solo administrador (anónimo -> 401, otros -> 403)."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return es_administrador(request.user)


class PermisoPartido(BasePermission):
    """
    - anónimo: solo GET (escribir -> 401, lo da la autenticación JWT)
    - planillero: GET y PATCH de goles_local, goles_visita y estado (otro campo -> 403)
    - administrador: todo
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if not request.user or not request.user.is_authenticated:
            return False
        if es_administrador(request.user):
            return True
        return es_planillero(request.user) and request.method == "PATCH"

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS or es_administrador(request.user):
            return True
        # Planillero: solo puede enviar los campos del marcador.
        return set(request.data.keys()) <= CAMPOS_PLANILLERO
