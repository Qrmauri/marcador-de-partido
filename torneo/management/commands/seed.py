"""Datos de demostración (solo desarrollo): python manage.py seed"""
from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand
from django.utils import timezone

from torneo.models import Equipo, Jugador, Liga, Partido


class Command(BaseCommand):
    help = "Crea una liga de ejemplo y usuarios de cada rol (solo desarrollo)."

    def add_arguments(self, parser):
        parser.add_argument("--password", default="Marcador2026!")

    def handle(self, *args, **opts):
        pw = opts["password"]
        admin, _ = User.objects.get_or_create(username="admin", defaults={"is_staff": True, "is_superuser": True})
        admin.set_password(pw); admin.save()
        plan, _ = User.objects.get_or_create(username="planillero")
        plan.set_password(pw); plan.save()
        plan.groups.add(Group.objects.get(name="planillero"))
        User.objects.get_or_create(username="lector")[0].set_password(pw)
        lector = User.objects.get(username="lector"); lector.set_password(pw); lector.save()

        liga, _ = Liga.objects.get_or_create(nombre="Liga Austral", pais="Chile", temporada="2026")
        nombres = [("Cóndores", "Coyhaique"), ("Pumas", "Chile Chico"), ("Guanacos", "Cochrane"), ("Huemules", "Puerto Aysén")]
        equipos = [Equipo.objects.get_or_create(nombre=n, ciudad=c, liga=liga)[0] for n, c in nombres]
        posiciones = ["POR", "DEF", "MED", "DEL"]
        for e in equipos:
            for i, pos in enumerate(posiciones, start=1):
                Jugador.objects.get_or_create(equipo=e, numero=i, defaults={"nombre": f"Jugador {i} {e.nombre}", "posicion": pos})
        if not Partido.objects.exists():
            ahora = timezone.now()
            datos = [(0, 1, 2, 1, "finalizado", -7), (2, 3, 0, 0, "finalizado", -6),
                     (0, 2, 1, 1, "en_juego", 0), (1, 3, 0, 0, "programado", 3)]
            for l, v, gl, gv, est, dias in datos:
                Partido.objects.create(liga=liga, local=equipos[l], visita=equipos[v], goles_local=gl,
                                       goles_visita=gv, estado=est, fecha=ahora + timedelta(days=dias),
                                       estadio="Estadio Municipal")
        self.stdout.write(self.style.SUCCESS(f"Listo. Usuarios: admin / planillero / lector — clave: {pw}"))
