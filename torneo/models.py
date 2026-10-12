from django.core.exceptions import ValidationError
from django.db import models


class Liga(models.Model):
    nombre = models.CharField(max_length=100)
    pais = models.CharField(max_length=60)
    temporada = models.CharField(max_length=20)

    class Meta:
        ordering = ["nombre", "temporada"]

    def __str__(self):
        return f"{self.nombre} ({self.temporada})"


class Equipo(models.Model):
    nombre = models.CharField(max_length=100)
    ciudad = models.CharField(max_length=100)
    liga = models.ForeignKey(Liga, on_delete=models.CASCADE, related_name="equipos")

    class Meta:
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Jugador(models.Model):
    class Posicion(models.TextChoices):
        POR = "POR", "Portero"
        DEF = "DEF", "Defensa"
        MED = "MED", "Mediocampista"
        DEL = "DEL", "Delantero"

    nombre = models.CharField(max_length=100)
    numero = models.PositiveSmallIntegerField()
    posicion = models.CharField(max_length=3, choices=Posicion.choices)
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name="jugadores")

    class Meta:
        ordering = ["equipo__nombre", "numero"]
        verbose_name_plural = "jugadores"

    def __str__(self):
        return f"#{self.numero} {self.nombre}"


class Partido(models.Model):
    class Estado(models.TextChoices):
        PROGRAMADO = "programado", "Programado"
        EN_JUEGO = "en_juego", "En juego"
        FINALIZADO = "finalizado", "Finalizado"

    liga = models.ForeignKey(Liga, on_delete=models.CASCADE, related_name="partidos")
    local = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name="partidos_local")
    visita = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name="partidos_visita")
    fecha = models.DateTimeField()
    estadio = models.CharField(max_length=100, blank=True)
    goles_local = models.PositiveSmallIntegerField(default=0)
    goles_visita = models.PositiveSmallIntegerField(default=0)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PROGRAMADO)

    class Meta:
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.local} {self.goles_local} - {self.goles_visita} {self.visita}"

    def clean(self):
        """Reglas de negocio: un equipo no juega contra sí mismo y todo es de la misma liga."""
        super().clean()
        if self.local_id and self.visita_id and self.local_id == self.visita_id:
            raise ValidationError({"visita": "El equipo local y el visitante deben ser distintos."})
        if self.liga_id:
            if self.local_id and self.local.liga_id != self.liga_id:
                raise ValidationError({"local": "El equipo local no pertenece a la liga del partido."})
            if self.visita_id and self.visita.liga_id != self.liga_id:
                raise ValidationError({"visita": "El equipo visitante no pertenece a la liga del partido."})
