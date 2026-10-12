from rest_framework import serializers

from .models import Equipo, Jugador, Liga, Partido


class LigaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Liga
        fields = ["id", "nombre", "pais", "temporada"]


class EquipoSerializer(serializers.ModelSerializer):
    liga_nombre = serializers.CharField(source="liga.nombre", read_only=True)

    class Meta:
        model = Equipo
        fields = ["id", "nombre", "ciudad", "liga", "liga_nombre"]


class JugadorSerializer(serializers.ModelSerializer):
    equipo_nombre = serializers.CharField(source="equipo.nombre", read_only=True)

    class Meta:
        model = Jugador
        fields = ["id", "nombre", "numero", "posicion", "equipo", "equipo_nombre"]


class PartidoSerializer(serializers.ModelSerializer):
    liga_nombre = serializers.CharField(source="liga.nombre", read_only=True)
    local_nombre = serializers.CharField(source="local.nombre", read_only=True)
    visita_nombre = serializers.CharField(source="visita.nombre", read_only=True)

    class Meta:
        model = Partido
        fields = [
            "id", "liga", "liga_nombre", "local", "local_nombre", "visita", "visita_nombre",
            "fecha", "estadio", "goles_local", "goles_visita", "estado",
        ]

    def validate(self, attrs):
        """Mismas reglas de negocio que el modelo (también en PATCH parcial)."""
        get = lambda k: attrs.get(k, getattr(self.instance, k, None))  # noqa: E731
        liga, local, visita = get("liga"), get("local"), get("visita")
        if local and visita and local.pk == visita.pk:
            raise serializers.ValidationError({"visita": "Local y visita deben ser equipos distintos."})
        if liga and local and local.liga_id != liga.pk:
            raise serializers.ValidationError({"local": "El equipo local no pertenece a la liga."})
        if liga and visita and visita.liga_id != liga.pk:
            raise serializers.ValidationError({"visita": "El equipo visitante no pertenece a la liga."})
        return attrs
