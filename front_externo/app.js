/* Marcador en Vivo · front externo (HTML + CSS + JS, sin frameworks).
 *
 * Consume la API REST del proyecto Django. CONTRATO esperado (ver enunciado):
 *   POST  /token/            {username, password} -> {access, refresh}
 *   POST  /token/refresh/    {refresh}            -> {access}
 *   GET   /me/               (JWT)                -> {id, username, rol}
 *   GET   /ligas/                                  -> [{id, nombre, pais, temporada}]
 *   GET   /ligas/{id}/tabla/                       -> [{equipo_id, equipo, pj, pg, pe, pp, gf, gc, dg, pts}]
 *   GET   /equipos/?liga={id}                      -> [{id, nombre, ciudad, liga, liga_nombre}]
 *   GET   /jugadores/?equipo={id}                  -> [{id, nombre, numero, posicion, equipo, equipo_nombre}]
 *   GET   /partidos/?liga={id}&estado={estado}     -> [{id, liga, liga_nombre, local, local_nombre, visita,
 *                                                       visita_nombre, fecha, estadio, goles_local, goles_visita, estado}]
 *   PATCH /partidos/{id}/    (planillero o admin)  {goles_local, goles_visita, estado}
 *   POST  /partidos/         (admin)               {liga, local, visita, fecha, estadio, goles_local, goles_visita, estado}
 *   DELETE /partidos/{id}/   (admin)
 * Las listas pueden venir paginadas ({count, next, previous, results}) o como arreglo.
 */
(function () {
  "use strict";

  var API = String(window.API_URL || "http://127.0.0.1:8000/api").replace(/\/+$/, "");
  var REFRESCO_MS = 15000;
  var ESTADOS = { programado: "Programado", en_juego: "En juego", finalizado: "Finalizado" };
  var POSICIONES = { POR: "Portero", DEF: "Defensa", MED: "Mediocampista", DEL: "Delantero" };

  // sessionStorage: el token se borra al cerrar la pestaña (más seguro que localStorage).
  var almacen = window.sessionStorage;
  var estado = {
    usuario: null,          // {id, username, rol}
    ligas: [],
    ligaId: null,
    filtro: "",
    equipos: [],
    editando: {},           // partidoId -> {goles_local, goles_visita, estado} sin guardar
  };

  var $ = function (sel) { return document.querySelector(sel); };

  function esc(v) {
    return String(v == null ? "" : v).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  // ------------------------------------------------------------------ API
  function ErrorApi(status, mensaje, datos) {
    this.status = status; this.message = mensaje; this.datos = datos;
  }

  function explicar(status, datos) {
    var detalle = datos && (datos.detail || datos.non_field_errors ||
      (typeof datos === "object" ? Object.keys(datos).map(function (k) {
        return k + ": " + [].concat(datos[k]).join(" ");
      }).join(" · ") : datos));
    if (status === 0) {
      if (location.protocol === "file:") return "Abriste index.html como archivo (origen 'null'): ábrelo con Live Server o con 'python -m http.server 5500' en http://127.0.0.1:5500.";
      return "Sin respuesta de la API. ¿Está corriendo el servidor? ¿CORS_ALLOWED_ORIGINS incluye " + location.origin + "?";
    }
    if (status === 401) return "401 · No autenticado: inicia sesión (o el token venció).";
    if (status === 403) return "403 · Tu rol no tiene permiso para esta acción." + (detalle ? " " + detalle : "");
    if (status === 404) return "404 · No existe ese recurso en la API.";
    if (status === 400) return "400 · Datos inválidos: " + (detalle || "revisa el formulario.");
    if (status === 429) return "429 · Demasiadas peticiones (throttling). Espera un momento.";
    return status + " · " + (detalle || "Error inesperado de la API.");
  }

  function pedir(metodo, ruta, cuerpo, reintento) {
    var url = /^https?:/.test(ruta) ? ruta : API + ruta;
    var cabeceras = { "Accept": "application/json" };
    if (cuerpo !== undefined) cabeceras["Content-Type"] = "application/json";
    var access = almacen.getItem("access");
    if (access) cabeceras["Authorization"] = "Bearer " + access;

    return fetch(url, {
      method: metodo,
      headers: cabeceras,
      body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
    }).catch(function () {
      conexion(false);
      throw new ErrorApi(0, explicar(0));
    }).then(function (r) {
      conexion(true);
      if (r.status === 401 && access && !reintento && almacen.getItem("refresh")) {
        return refrescar().then(function () { return pedir(metodo, ruta, cuerpo, true); });
      }
      if (r.status === 204) return null;
      return r.text().then(function (txt) {
        var datos = null;
        try { datos = txt ? JSON.parse(txt) : null; } catch (e) { datos = txt; }
        if (!r.ok) throw new ErrorApi(r.status, explicar(r.status, datos), datos);
        return datos;
      });
    });
  }

  function refrescar() {
    return fetch(API + "/token/refresh/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh: almacen.getItem("refresh") }),
    }).then(function (r) {
      if (!r.ok) throw new ErrorApi(401, explicar(401));
      return r.json();
    }).then(function (d) {
      almacen.setItem("access", d.access);
      if (d.refresh) almacen.setItem("refresh", d.refresh);
    }).catch(function (e) {
      cerrarSesion(true);
      throw e;
    });
  }

  // Trae todas las páginas si la API está paginada.
  function listar(ruta) {
    var todos = [];
    function pagina(url) {
      return pedir("GET", url).then(function (d) {
        if (Array.isArray(d)) return d;
        if (d && Array.isArray(d.results)) {
          todos = todos.concat(d.results);
          return d.next ? pagina(d.next) : todos;
        }
        throw new ErrorApi(-1, "La respuesta de " + ruta + " no es una lista JSON.");
      });
    }
    return pagina(ruta);
  }

  // ------------------------------------------------------------------ UI comunes
  function conexion(ok) {
    var el = $("#conexion");
    el.classList.toggle("ok", ok);
    el.classList.toggle("caida", !ok);
    el.lastElementChild.textContent = ok ? "API conectada" : "API sin conexión";
  }

  function aviso(texto, tipo) {
    var t = document.createElement("div");
    t.className = "toast " + (tipo || "info");
    t.textContent = texto;
    $("#toasts").appendChild(t);
    setTimeout(function () { t.classList.add("sale"); }, 4200);
    setTimeout(function () { t.remove(); }, 4800);
  }

  function falla(e) { aviso(e.message || String(e), "error"); }

  function fecha(iso) {
    var d = new Date(iso);
    if (isNaN(d)) return esc(iso);
    return d.toLocaleString("es-CL", { weekday: "short", day: "2-digit", month: "2-digit",
                                        hour: "2-digit", minute: "2-digit" });
  }

  function esPlanillero() { return estado.usuario && (estado.usuario.rol === "planillero" || estado.usuario.rol === "administrador"); }
  function esAdmin() { return estado.usuario && estado.usuario.rol === "administrador"; }

  // ------------------------------------------------------------------ sesión
  function pintarSesion() {
    var cont = $("#sesion");
    if (!estado.usuario) {
      cont.innerHTML = '<button class="btn" id="btn-login">Iniciar sesión</button>';
      $("#btn-login").onclick = function () { $("#login-error").hidden = true; $("#dlg-login").showModal(); };
    } else {
      cont.innerHTML = '<span class="usuario">' + esc(estado.usuario.username) +
        ' <span class="rol rol-' + esc(estado.usuario.rol) + '">' + esc(estado.usuario.rol) + "</span></span>" +
        '<button class="btn secundario" id="btn-salir">Salir</button>';
      $("#btn-salir").onclick = function () { cerrarSesion(false); };
    }
    $("#form-nuevo").hidden = !esAdmin();
  }

  function cargarUsuario() {
    if (!almacen.getItem("access")) { estado.usuario = null; pintarSesion(); return Promise.resolve(); }
    return pedir("GET", "/me/").then(function (u) {
      estado.usuario = u;
    }).catch(function () {
      estado.usuario = null;
    }).then(pintarSesion);
  }

  function cerrarSesion(vencida) {
    almacen.removeItem("access");
    almacen.removeItem("refresh");
    estado.usuario = null;
    estado.editando = {};
    pintarSesion();
    pintarPartidos(estado.ultimosPartidos || []);
    if (vencida) aviso("La sesión venció: vuelve a iniciar sesión.", "error");
  }

  $("#form-login").addEventListener("submit", function (ev) {
    ev.preventDefault();
    var f = ev.target;
    var err = $("#login-error");
    err.hidden = true;
    fetch(API + "/token/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: f.username.value.trim(), password: f.password.value }),
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (d) {
        if (!r.ok) throw new ErrorApi(r.status, r.status === 401 ? "Usuario o contraseña incorrectos." : explicar(r.status, d));
        if (!d.access || !d.refresh) throw new ErrorApi(-1, "La API no devolvió {access, refresh}.");
        almacen.setItem("access", d.access);
        almacen.setItem("refresh", d.refresh);
      });
    }, function () {
      throw new ErrorApi(0, explicar(0));
    }).then(function () {
      f.reset();
      $("#dlg-login").close();
      return cargarUsuario();
    }).then(function () {
      aviso("Hola, " + estado.usuario.username + " (" + estado.usuario.rol + ")", "ok");
      cargarPartidos();
      cargarEquipos();
    }).catch(function (e) {
      err.textContent = e.message;
      err.hidden = false;
    });
  });
  $("#btn-cancelar-login").onclick = function () { $("#dlg-login").close(); };

  // ------------------------------------------------------------------ ligas
  function cargarLigas() {
    return listar("/ligas/").then(function (ligas) {
      estado.ligas = ligas;
      if (!ligas.length) {
        $("#ligas").innerHTML = '<span class="vacio">La API no tiene ligas todavía.</span>';
        return;
      }
      if (!ligas.some(function (l) { return l.id === estado.ligaId; })) estado.ligaId = ligas[0].id;
      pintarLigas();
    });
  }

  function pintarLigas() {
    $("#ligas").innerHTML = estado.ligas.map(function (l) {
      return '<button class="liga' + (l.id === estado.ligaId ? " activa" : "") + '" data-id="' + l.id + '">' +
        esc(l.nombre) + " <small>" + esc(l.temporada) + "</small></button>";
    }).join("");
  }

  $("#ligas").addEventListener("click", function (ev) {
    var b = ev.target.closest("button.liga");
    if (!b) return;
    estado.ligaId = Number(b.dataset.id);
    estado.editando = {};
    pintarLigas();
    cargarTodoDeLaLiga();
  });

  // ------------------------------------------------------------------ partidos
  function cargarPartidos() {
    if (!estado.ligaId) return Promise.resolve();
    var q = "?liga=" + estado.ligaId + (estado.filtro ? "&estado=" + estado.filtro : "");
    return listar("/partidos/" + q).then(function (lista) {
      estado.ultimosPartidos = lista;
      pintarPartidos(lista);
    }).catch(falla);
  }

  function pintarPartidos(lista) {
    var cont = $("#partidos");
    if (!lista.length) { cont.innerHTML = '<p class="vacio">No hay partidos para este filtro.</p>'; return; }
    var orden = { en_juego: 0, programado: 1, finalizado: 2 };
    lista = lista.slice().sort(function (a, b) {
      return (orden[a.estado] - orden[b.estado]) || (new Date(a.fecha) - new Date(b.fecha));
    });
    cont.innerHTML = lista.map(tarjetaPartido).join("");
  }

  function tarjetaPartido(p) {
    var e = estado.editando[p.id];
    var gl = e ? e.goles_local : p.goles_local;
    var gv = e ? e.goles_visita : p.goles_visita;
    var est = e ? e.estado : p.estado;
    var controles = "";
    if (esPlanillero()) {
      controles = '<div class="planilla" data-id="' + p.id + '">' +
        '<div class="ajuste"><button data-acc="menos" data-lado="goles_local" aria-label="Restar gol local">−</button>' +
        '<button data-acc="mas" data-lado="goles_local" aria-label="Sumar gol local">+</button></div>' +
        '<select data-acc="estado">' + Object.keys(ESTADOS).map(function (k) {
          return '<option value="' + k + '"' + (k === est ? " selected" : "") + ">" + ESTADOS[k] + "</option>";
        }).join("") + "</select>" +
        '<div class="ajuste"><button data-acc="menos" data-lado="goles_visita" aria-label="Restar gol visita">−</button>' +
        '<button data-acc="mas" data-lado="goles_visita" aria-label="Sumar gol visita">+</button></div>' +
        '<button class="btn chico" data-acc="guardar"' + (e ? "" : " disabled") + ">Guardar</button>" +
        (esAdmin() ? '<button class="btn chico peligro" data-acc="borrar">Borrar</button>' : "") +
        "</div>";
    }
    return '<article class="partido est-' + esc(p.estado) + (e ? " sucio" : "") + '">' +
      '<div class="p-cab"><span>' + fecha(p.fecha) + (p.estadio ? " · " + esc(p.estadio) : "") + "</span>" +
      '<span class="p-estado">' + (p.estado === "en_juego" ? '<span class="vivo"></span>' : "") +
      esc(ESTADOS[p.estado] || p.estado) + "</span></div>" +
      '<div class="p-marcador"><span class="p-equipo">' + esc(p.local_nombre) + "</span>" +
      '<span class="p-goles"><b>' + esc(gl) + "</b><i>:</i><b>" + esc(gv) + "</b></span>" +
      '<span class="p-equipo visita">' + esc(p.visita_nombre) + "</span></div>" +
      controles + "</article>";
  }

  $("#partidos").addEventListener("click", function (ev) {
    var b = ev.target.closest("button[data-acc]");
    if (!b) return;
    var cont = b.closest(".planilla");
    var id = Number(cont.dataset.id);
    var p = (estado.ultimosPartidos || []).find(function (x) { return x.id === id; });
    if (!p) return;
    var e = estado.editando[id] || { goles_local: p.goles_local, goles_visita: p.goles_visita, estado: p.estado };
    var acc = b.dataset.acc;
    if (acc === "mas" || acc === "menos") {
      e[b.dataset.lado] = Math.max(0, e[b.dataset.lado] + (acc === "mas" ? 1 : -1));
      if (e.estado === "programado" && acc === "mas") e.estado = "en_juego";
      estado.editando[id] = e;
      pintarPartidos(estado.ultimosPartidos);
    } else if (acc === "guardar") {
      b.disabled = true;
      pedir("PATCH", "/partidos/" + id + "/", e).then(function (actualizado) {
        delete estado.editando[id];
        aviso("Marcador guardado: " + actualizado.local_nombre + " " + actualizado.goles_local +
              " - " + actualizado.goles_visita + " " + actualizado.visita_nombre, "ok");
        return Promise.all([cargarPartidos(), cargarTabla()]);
      }).catch(function (err) { b.disabled = false; falla(err); });
    } else if (acc === "borrar") {
      if (!confirm("¿Borrar " + p.local_nombre + " vs " + p.visita_nombre + "?")) return;
      pedir("DELETE", "/partidos/" + id + "/").then(function () {
        aviso("Partido borrado.", "ok");
        return Promise.all([cargarPartidos(), cargarTabla()]);
      }).catch(falla);
    }
  });

  $("#partidos").addEventListener("change", function (ev) {
    var s = ev.target.closest("select[data-acc=estado]");
    if (!s) return;
    var id = Number(s.closest(".planilla").dataset.id);
    var p = estado.ultimosPartidos.find(function (x) { return x.id === id; });
    var e = estado.editando[id] || { goles_local: p.goles_local, goles_visita: p.goles_visita, estado: p.estado };
    e.estado = s.value;
    estado.editando[id] = e;
    pintarPartidos(estado.ultimosPartidos);
  });

  $("#filtros").addEventListener("click", function (ev) {
    var b = ev.target.closest(".chip");
    if (!b) return;
    document.querySelectorAll("#filtros .chip").forEach(function (c) { c.classList.toggle("activo", c === b); });
    estado.filtro = b.dataset.estado;
    cargarPartidos();
  });

  $("#form-nuevo").addEventListener("submit", function (ev) {
    ev.preventDefault();
    var f = ev.target;
    var cuerpo = {
      liga: estado.ligaId,
      local: Number(f.local.value),
      visita: Number(f.visita.value),
      fecha: new Date(f.fecha.value).toISOString(),
      estadio: f.estadio.value.trim(),
      goles_local: 0, goles_visita: 0, estado: "programado",
    };
    pedir("POST", "/partidos/", cuerpo).then(function (p) {
      aviso("Partido creado (id " + p.id + ").", "ok");
      f.reset();
      if (f.visita.options.length > 1) f.visita.selectedIndex = 1;
      return cargarPartidos();
    }).catch(falla);
  });

  // ------------------------------------------------------------------ tabla
  function cargarTabla() {
    if (!estado.ligaId) return Promise.resolve();
    return pedir("GET", "/ligas/" + estado.ligaId + "/tabla/").then(function (filas) {
      filas = Array.isArray(filas) ? filas : (filas && filas.results) || [];
      if (!filas.length) { $("#tabla").innerHTML = '<p class="vacio">Sin equipos.</p>'; return; }
      $("#tabla").innerHTML = '<table class="posiciones"><thead><tr><th>#</th><th>Equipo</th>' +
        "<th>PJ</th><th>G</th><th>E</th><th>P</th><th>DG</th><th>Pts</th></tr></thead><tbody>" +
        filas.map(function (f, i) {
          return "<tr><td>" + (i + 1) + "</td><td>" + esc(f.equipo) + "</td><td>" + esc(f.pj) +
            "</td><td>" + esc(f.pg) + "</td><td>" + esc(f.pe) + "</td><td>" + esc(f.pp) +
            "</td><td>" + (f.dg > 0 ? "+" : "") + esc(f.dg) + "</td><td><b>" + esc(f.pts) + "</b></td></tr>";
        }).join("") + "</tbody></table>";
    }).catch(function (e) {
      $("#tabla").innerHTML = '<p class="vacio">No se pudo cargar la tabla: ' + esc(e.message) + "</p>";
    });
  }

  // ------------------------------------------------------------------ equipos
  function cargarEquipos() {
    if (!estado.ligaId) return Promise.resolve();
    return listar("/equipos/?liga=" + estado.ligaId).then(function (equipos) {
      estado.equipos = equipos;
      $("#equipos").innerHTML = equipos.map(function (e) {
        return '<details data-id="' + e.id + '"><summary><b>' + esc(e.nombre) + "</b> <small>" +
          esc(e.ciudad) + '</small></summary><div class="plantel">Cargando…</div></details>';
      }).join("") || '<p class="vacio">Sin equipos.</p>';
      var opciones = equipos.map(function (e) {
        return '<option value="' + e.id + '">' + esc(e.nombre) + "</option>";
      }).join("");
      $("#form-nuevo").local.innerHTML = opciones;
      $("#form-nuevo").visita.innerHTML = opciones;
      if (equipos.length > 1) $("#form-nuevo").visita.selectedIndex = 1;
    }).catch(falla);
  }

  $("#equipos").addEventListener("toggle", function (ev) {
    var d = ev.target;
    if (!d.open || d.dataset.cargado) return;
    listar("/jugadores/?equipo=" + d.dataset.id).then(function (js) {
      d.dataset.cargado = "1";
      d.querySelector(".plantel").innerHTML = js.length ? "<ul>" + js.map(function (j) {
        return '<li><span class="num">' + esc(j.numero) + "</span>" + esc(j.nombre) +
          " <small>" + esc(POSICIONES[j.posicion] || j.posicion) + "</small></li>";
      }).join("") + "</ul>" : '<p class="vacio">Sin jugadores.</p>';
    }).catch(function (e) { d.querySelector(".plantel").textContent = e.message; });
  }, true);

  // ------------------------------------------------------------------ diagnóstico
  var CONTRATO = {
    "/ligas/": ["id", "nombre", "pais", "temporada"],
    "/equipos/": ["id", "nombre", "ciudad", "liga", "liga_nombre"],
    "/jugadores/": ["id", "nombre", "numero", "posicion", "equipo", "equipo_nombre"],
    "/partidos/": ["id", "liga", "liga_nombre", "local", "local_nombre", "visita", "visita_nombre",
                   "fecha", "estadio", "goles_local", "goles_visita", "estado"],
  };

  $("#btn-diagnostico").onclick = function () {
    var ul = $("#diagnostico");
    ul.innerHTML = "";
    function linea(ok, texto) {
      var li = document.createElement("li");
      li.className = ok ? "ok" : "mal";
      li.textContent = (ok ? "✓ " : "✗ ") + texto;
      ul.appendChild(li);
    }
    var pruebas = Object.keys(CONTRATO).map(function (ruta) {
      return function () {
        return pedir("GET", ruta).then(function (d) {
          var lista = Array.isArray(d) ? d : d && d.results;
          if (!Array.isArray(lista)) return linea(false, "GET " + ruta + " no devuelve una lista JSON");
          if (!lista.length) return linea(true, "GET " + ruta + " responde (sin datos para revisar campos)");
          var faltan = CONTRATO[ruta].filter(function (c) { return !(c in lista[0]); });
          linea(!faltan.length, "GET " + ruta + (faltan.length ? " · faltan campos: " + faltan.join(", ") : " · campos OK" +
                (Array.isArray(d) ? "" : " · paginada")));
        }).catch(function (e) { linea(false, "GET " + ruta + " · " + e.message); });
      };
    });
    pruebas.push(function () {
      if (!estado.ligaId) return linea(false, "GET /ligas/{id}/tabla/ · no hay ligas");
      return pedir("GET", "/ligas/" + estado.ligaId + "/tabla/").then(function (d) {
        var f = (Array.isArray(d) ? d : (d && d.results) || [])[0] || {};
        var faltan = ["equipo", "pj", "pg", "pe", "pp", "dg", "pts"].filter(function (c) { return !(c in f); });
        linea(!faltan.length, "GET /ligas/{id}/tabla/" + (faltan.length ? " · faltan: " + faltan.join(", ") : " · OK"));
      }).catch(function (e) { linea(false, "GET /ligas/{id}/tabla/ · " + e.message); });
    });
    pruebas.push(function () {
      return fetch(API + "/me/").then(function (r) {
        linea(r.status === 401, "GET /me/ sin token responde " + r.status + (r.status === 401 ? " (correcto)" : " (se esperaba 401)"));
      }).catch(function () { linea(false, "GET /me/ · sin respuesta (¿CORS?)"); });
    });
    pruebas.push(function () {
      return fetch(API + "/ligas/", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" })
        .then(function (r) {
          linea(r.status === 401, "POST /ligas/ sin token responde " + r.status + (r.status === 401 ? " (correcto)" : " (se esperaba 401)"));
        }).catch(function () { linea(false, "POST /ligas/ · sin respuesta (¿CORS?)"); });
    });
    if (estado.usuario) {
      pruebas.push(function () {
        return pedir("GET", "/me/").then(function (u) {
          linea(["administrador", "planillero", "lector"].indexOf(u.rol) >= 0, "GET /me/ con token · rol = " + u.rol);
        }).catch(function (e) { linea(false, "GET /me/ con token · " + e.message); });
      });
    }
    pruebas.reduce(function (p, f) { return p.then(f); }, Promise.resolve());
  };

  // ------------------------------------------------------------------ arranque
  function cargarTodoDeLaLiga() {
    return Promise.all([cargarPartidos(), cargarTabla(), cargarEquipos()]);
  }

  $("#api-url").textContent = API;

  // Abierto con doble clic (file://): el navegador manda "Origin: null" y CORS lo bloquea.
  if (location.protocol === "file:") {
    var aviso_file = document.createElement("div");
    aviso_file.className = "aviso-file";
    aviso_file.innerHTML = "<strong>Este front está abierto como archivo (file://).</strong> El navegador envía " +
      "<code>Origin: null</code> y la API lo bloquea por CORS. Ábrelo desde un servidor web: " +
      "<b>Live Server</b> en VS Code, o en esta carpeta <code>python -m http.server 5500</code> y entra a " +
      "<code>http://127.0.0.1:5500</code>.";
    document.body.insertBefore(aviso_file, document.querySelector(".ligas"));
  }
  cargarUsuario()
    .then(cargarLigas)
    .then(cargarTodoDeLaLiga)
    .catch(falla);

  // "En vivo": refresca partidos y tabla (sin pisar lo que el planillero está editando).
  setInterval(function () {
    if (document.hidden || !estado.ligaId) return;
    cargarPartidos();
    cargarTabla();
  }, REFRESCO_MS);
})();
