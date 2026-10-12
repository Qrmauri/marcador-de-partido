from datetime import timedelta

from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Equipo, Liga, Partido


class BaseDatos(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.liga = Liga.objects.create(nombre="L", pais="CL", temporada="2026")
        cls.a, cls.b, cls.c = (Equipo.objects.create(nombre=n, ciudad="X", liga=cls.liga) for n in "ABC")
        ahora = timezone.now()
        cls.p1 = Partido.objects.create(liga=cls.liga, local=cls.a, visita=cls.b, goles_local=2,
                                        goles_visita=1, estado="finalizado", fecha=ahora)
        cls.p2 = Partido.objects.create(liga=cls.liga, local=cls.b, visita=cls.c, goles_local=1,
                                        goles_visita=1, estado="finalizado", fecha=ahora)
        cls.p3 = Partido.objects.create(liga=cls.liga, local=cls.a, visita=cls.c, goles_local=5,
                                        goles_visita=0, estado="en_juego", fecha=ahora)  # no cuenta
        User.objects.create_superuser("adm", password="x12345678")
        pl = User.objects.create_user("pla", password="x12345678")
        pl.groups.add(Group.objects.get(name="planillero"))
        User.objects.create_user("lec", password="x12345678")

    def token(self, user):
        r = APIClient().post("/api/token/", {"username": user, "password": "x12345678"}, format="json")
        self.assertEqual(r.status_code, 200)
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION="Bearer " + r.json()["access"])
        return c


class ApiTests(BaseDatos):
    def test_login_invalido_401(self):
        r = APIClient().post("/api/token/", {"username": "adm", "password": "mal"}, format="json")
        self.assertEqual(r.status_code, 401)

    def test_me_roles(self):
        self.assertEqual(APIClient().get("/api/me/").status_code, 401)
        self.assertEqual(self.token("adm").get("/api/me/").json()["rol"], "administrador")
        self.assertEqual(self.token("pla").get("/api/me/").json()["rol"], "planillero")
        self.assertEqual(self.token("lec").get("/api/me/").json()["rol"], "lector")

    def test_lectura_publica_y_contrato(self):
        r = APIClient().get("/api/partidos/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(set(r.json()["results"][0]), {
            "id", "liga", "liga_nombre", "local", "local_nombre", "visita", "visita_nombre",
            "fecha", "estadio", "goles_local", "goles_visita", "estado"})

    def test_tabla(self):
        t = APIClient().get(f"/api/ligas/{self.liga.pk}/tabla/").json()
        a = next(f for f in t if f["equipo"] == "A")
        self.assertEqual((a["pj"], a["pg"], a["pts"], a["dg"]), (1, 1, 3, 1))
        b = next(f for f in t if f["equipo"] == "B")
        self.assertEqual((b["pj"], b["pg"], b["pe"], b["pp"], b["pts"]), (2, 0, 1, 1, 1))
        self.assertEqual(t[0]["equipo"], "A")

    def test_filtros_y_errores(self):
        c = APIClient()
        self.assertEqual(len(c.get(f"/api/partidos/?estado=finalizado").json()["results"]), 2)
        self.assertEqual(c.get("/api/partidos/?estado=zzz").status_code, 400)
        self.assertEqual(c.get("/api/partidos/?liga=abc").status_code, 400)
        self.assertEqual(c.get("/api/partidos/99999/").status_code, 404)

    def test_permisos_partido(self):
        url = f"/api/partidos/{self.p3.pk}/"
        self.assertEqual(APIClient().patch(url, {"goles_local": 1}, format="json").status_code, 401)
        self.assertEqual(self.token("lec").patch(url, {"goles_local": 1}, format="json").status_code, 403)
        pl = self.token("pla")
        self.assertEqual(pl.patch(url, {"goles_local": 6, "estado": "finalizado"}, format="json").status_code, 200)
        self.assertEqual(pl.patch(url, {"estadio": "hack"}, format="json").status_code, 403)
        self.assertEqual(pl.patch(url, {"estado": "nada"}, format="json").status_code, 400)
        self.assertEqual(pl.delete(url).status_code, 403)
        self.assertEqual(pl.post("/api/partidos/", {}, format="json").status_code, 403)

    def test_admin_crud(self):
        ad = self.token("adm")
        datos = {"liga": self.liga.pk, "local": self.a.pk, "visita": self.c.pk,
                 "fecha": (timezone.now() + timedelta(days=1)).isoformat(), "estadio": "E",
                 "goles_local": 0, "goles_visita": 0, "estado": "programado"}
        r = ad.post("/api/partidos/", datos, format="json")
        self.assertEqual(r.status_code, 201)
        pk = r.json()["id"]
        self.assertEqual(ad.put(f"/api/partidos/{pk}/", {**datos, "estadio": "N"}, format="json").status_code, 200)
        malo = ad.post("/api/partidos/", {**datos, "visita": self.a.pk}, format="json")
        self.assertEqual(malo.status_code, 400)
        self.assertEqual(ad.delete(f"/api/partidos/{pk}/").status_code, 204)
        self.assertEqual(ad.post("/api/ligas/", {"nombre": "N", "pais": "CL", "temporada": "1"}, format="json").status_code, 201)
        self.assertEqual(self.token("pla").post("/api/ligas/", {"nombre": "N"}, format="json").status_code, 403)

    def test_cors(self):
        r = APIClient().get("/api/ligas/", HTTP_ORIGIN="http://127.0.0.1:5500")
        self.assertEqual(r["Access-Control-Allow-Origin"], "http://127.0.0.1:5500")
        r = APIClient().get("/api/ligas/", HTTP_ORIGIN="http://malo.com")
        self.assertNotIn("Access-Control-Allow-Origin", r)


class SitioTests(BaseDatos):
    def test_publico_mira(self):
        for n in ("partido_list", "liga_list", "equipo_list", "jugador_list"):
            self.assertEqual(self.client.get(reverse(n)).status_code, 200)
        self.assertEqual(self.client.get(reverse("partido_detail", args=[self.p1.pk])).status_code, 200)

    def test_sin_sesion_redirige(self):
        for n, a in (("partido_create", []), ("partido_update", [self.p1.pk]), ("partido_delete", [self.p1.pk]),
                     ("partido_marcador", [self.p1.pk])):
            r = self.client.get(reverse(n, args=a))
            self.assertEqual(r.status_code, 302)
            self.assertIn("/accounts/login/", r["Location"])

    def test_lector_403_planillero_marcador(self):
        self.client.login(username="lec", password="x12345678")
        self.assertEqual(self.client.get(reverse("partido_create")).status_code, 403)
        self.assertEqual(self.client.get(reverse("partido_marcador", args=[self.p3.pk])).status_code, 403)
        self.client.login(username="pla", password="x12345678")
        self.assertEqual(self.client.get(reverse("partido_create")).status_code, 403)
        r = self.client.post(reverse("partido_marcador", args=[self.p3.pk]),
                             {"goles_local": 9, "goles_visita": 9, "estado": "finalizado"})
        self.assertEqual(r.status_code, 302)
        self.p3.refresh_from_db()
        self.assertEqual(self.p3.goles_local, 9)

    def test_admin_crud_sitio(self):
        self.client.login(username="adm", password="x12345678")
        r = self.client.post(reverse("partido_create"), {
            "liga": self.liga.pk, "local": self.a.pk, "visita": self.b.pk, "fecha": "2026-11-01T18:00",
            "estadio": "E", "goles_local": 0, "goles_visita": 0, "estado": "programado"})
        self.assertEqual(r.status_code, 302)
        p = Partido.objects.latest("id")
        self.assertEqual(self.client.post(reverse("partido_delete", args=[p.pk])).status_code, 302)
        self.assertEqual(self.client.get(reverse("liga_create")).status_code, 200)
