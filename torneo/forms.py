from django import forms

from .models import Equipo, Jugador, Liga, Partido

FORMATO_FECHA = "%Y-%m-%dT%H:%M"


class LigaForm(forms.ModelForm):
    class Meta:
        model = Liga
        fields = ["nombre", "pais", "temporada"]


class EquipoForm(forms.ModelForm):
    class Meta:
        model = Equipo
        fields = ["nombre", "ciudad", "liga"]


class JugadorForm(forms.ModelForm):
    class Meta:
        model = Jugador
        fields = ["nombre", "numero", "posicion", "equipo"]


class PartidoForm(forms.ModelForm):
    fecha = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format=FORMATO_FECHA),
        input_formats=[FORMATO_FECHA, "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"],
    )

    class Meta:
        model = Partido
        fields = ["liga", "local", "visita", "fecha", "estadio", "goles_local", "goles_visita", "estado"]


class MarcadorForm(forms.ModelForm):
    """Lo ÚNICO que puede tocar un planillero."""

    class Meta:
        model = Partido
        fields = ["goles_local", "goles_visita", "estado"]
