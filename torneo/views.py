"""Sitio HTML: vistas genéricas basadas en clases + control de roles."""
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView,
)

from .forms import EquipoForm, JugadorForm, LigaForm, MarcadorForm, PartidoForm
from .models import Equipo, Jugador, Liga, Partido
from .roles import AdministradorRequeridoMixin, PlanilleroOAdminRequeridoMixin


def _valor(obj, atributo):
    v = getattr(obj, atributo)
    return v() if callable(v) else v


# ---------------------------------------------------------------- Partido
class PartidoListView(ListView):
    model = Partido
    template_name = "torneo/partido_list.html"
    context_object_name = "partidos"
    paginate_by = 20

    def get_queryset(self):
        qs = Partido.objects.select_related("liga", "local", "visita")
        liga, estado = self.request.GET.get("liga"), self.request.GET.get("estado")
        if liga and liga.isdigit():
            qs = qs.filter(liga_id=liga)
        if estado in Partido.Estado.values:
            qs = qs.filter(estado=estado)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["ligas"] = Liga.objects.all()
        ctx["estados"] = Partido.Estado.choices
        ctx["liga_sel"] = self.request.GET.get("liga", "")
        ctx["estado_sel"] = self.request.GET.get("estado", "")
        return ctx


class PartidoDetailView(DetailView):
    model = Partido
    template_name = "torneo/partido_detail.html"
    queryset = Partido.objects.select_related("liga", "local", "visita")


class PartidoCreateView(AdministradorRequeridoMixin, CreateView):
    model = Partido
    form_class = PartidoForm
    template_name = "torneo/form.html"
    success_url = reverse_lazy("partido_list")
    extra_context = {"titulo": "Nuevo partido", "url_cancelar": "partido_list"}

    def form_valid(self, form):
        messages.success(self.request, "Partido creado.")
        return super().form_valid(form)


class PartidoUpdateView(AdministradorRequeridoMixin, UpdateView):
    model = Partido
    form_class = PartidoForm
    template_name = "torneo/form.html"
    success_url = reverse_lazy("partido_list")
    extra_context = {"titulo": "Editar partido", "url_cancelar": "partido_list"}

    def form_valid(self, form):
        messages.success(self.request, "Partido actualizado.")
        return super().form_valid(form)


class PartidoDeleteView(AdministradorRequeridoMixin, DeleteView):
    model = Partido
    template_name = "torneo/confirmar_borrar.html"
    success_url = reverse_lazy("partido_list")
    extra_context = {"url_cancelar": "partido_list"}

    def form_valid(self, form):
        messages.success(self.request, "Partido eliminado.")
        return super().form_valid(form)


class MarcadorUpdateView(PlanilleroOAdminRequeridoMixin, UpdateView):
    """El planillero actualiza SOLO goles y estado."""
    model = Partido
    form_class = MarcadorForm
    template_name = "torneo/marcador_form.html"

    def get_success_url(self):
        return reverse_lazy("partido_detail", args=[self.object.pk])

    def form_valid(self, form):
        messages.success(self.request, "Marcador actualizado.")
        return super().form_valid(form)


# ------------------------------------- CRUD de Liga / Equipo / Jugador
def construir_crud(prefijo, modelo, form, singular, plural, columnas, select=()):
    """Genera las 5 vistas genéricas (lista, detalle, crear, editar, borrar) de un modelo."""
    nombre_lista = f"{prefijo}_list"

    class Lista(ListView):
        model = modelo
        template_name = "torneo/lista.html"
        paginate_by = 30

        def get_queryset(self):
            return modelo.objects.select_related(*select)

        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            ctx.update(
                titulo=plural.capitalize(), prefijo=prefijo, singular=singular,
                encabezados=[c[0] for c in columnas],
                filas=[
                    {"obj": o, "valores": [_valor(o, c[1]) for c in columnas]}
                    for o in ctx["object_list"]
                ],
            )
            return ctx

    class Detalle(DetailView):
        model = modelo
        template_name = "torneo/detalle.html"

        def get_context_data(self, **kwargs):
            ctx = super().get_context_data(**kwargs)
            ctx.update(
                titulo=str(self.object), prefijo=prefijo,
                campos=[(c[0], _valor(self.object, c[1])) for c in columnas],
            )
            return ctx

    class Crear(AdministradorRequeridoMixin, CreateView):
        model = modelo
        form_class = form
        template_name = "torneo/form.html"
        success_url = reverse_lazy(nombre_lista)
        extra_context = {"titulo": f"Nuevo {singular}", "url_cancelar": nombre_lista}

        def form_valid(self, f):
            messages.success(self.request, f"{singular.capitalize()} creado.")
            return super().form_valid(f)

    class Editar(AdministradorRequeridoMixin, UpdateView):
        model = modelo
        form_class = form
        template_name = "torneo/form.html"
        success_url = reverse_lazy(nombre_lista)
        extra_context = {"titulo": f"Editar {singular}", "url_cancelar": nombre_lista}

        def form_valid(self, f):
            messages.success(self.request, f"{singular.capitalize()} actualizado.")
            return super().form_valid(f)

    class Borrar(AdministradorRequeridoMixin, DeleteView):
        model = modelo
        template_name = "torneo/confirmar_borrar.html"
        success_url = reverse_lazy(nombre_lista)
        extra_context = {"url_cancelar": nombre_lista}

        def form_valid(self, f):
            messages.success(self.request, f"{singular.capitalize()} eliminado.")
            return super().form_valid(f)

    return Lista, Detalle, Crear, Editar, Borrar


(LigaListView, LigaDetailView, LigaCreateView, LigaUpdateView, LigaDeleteView) = construir_crud(
    "liga", Liga, LigaForm, "liga", "ligas",
    [("Nombre", "nombre"), ("País", "pais"), ("Temporada", "temporada")],
)
(EquipoListView, EquipoDetailView, EquipoCreateView, EquipoUpdateView, EquipoDeleteView) = construir_crud(
    "equipo", Equipo, EquipoForm, "equipo", "equipos",
    [("Nombre", "nombre"), ("Ciudad", "ciudad"), ("Liga", "liga")], select=("liga",),
)
(JugadorListView, JugadorDetailView, JugadorCreateView, JugadorUpdateView, JugadorDeleteView) = construir_crud(
    "jugador", Jugador, JugadorForm, "jugador", "jugadores",
    [("Nombre", "nombre"), ("Número", "numero"), ("Posición", "get_posicion_display"), ("Equipo", "equipo")],
    select=("equipo",),
)
