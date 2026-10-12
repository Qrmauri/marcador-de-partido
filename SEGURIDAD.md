# SEGURIDAD.md — Marcador en Vivo (Evaluación 3)

## 1. Herramienta de IA usada
Claude (Anthropic).  <!-- Ajusta si usaste otra herramienta -->

## 2. Prompt enviado a la IA
> Actúa como auditor de seguridad de aplicaciones web. Revisa este proyecto Django +
> Django REST Framework (API de marcadores deportivos con JWT y un front externo en
> http://127.0.0.1:5500). Revisa `settings.py`, `permissions.py`, `api_views.py`,
> `serializers.py` y las vistas del sitio. Dame recomendaciones concretas y priorizadas
> sobre: manejo de SECRET_KEY y DEBUG, CORS, autenticación JWT (vida de los tokens),
> permisos por rol, validación de entradas, throttling/abuso, exposición de datos y
> cabeceras/cookies. Para cada una indica el riesgo y cómo corregirlo en el código.

## 3. Recomendaciones recibidas y dónde se aplicaron

| # | Recomendación | Dónde se aplicó |
|---|---------------|-----------------|
| 1 | No dejar `SECRET_KEY` ni `DEBUG` fijos en el código; leerlos del entorno. Con `DEBUG=0` exigir una clave real. | `marcador/settings.py` (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`; lanza `ImproperlyConfigured` si falta la clave en producción). La clave por defecto solo existe en modo desarrollo. |
| 2 | CORS restringido al origen del front; nunca `CORS_ALLOW_ALL_ORIGINS`. | `settings.py`: `CORS_ALLOWED_ORIGINS = ["http://127.0.0.1:5500", "http://localhost:5500"]` y `CORS_ALLOW_ALL_ORIGINS = False`. Probado en `tests.py::test_cors`. |
| 3 | Access token de vida corta. | `settings.py`: `SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = 30 min` (máx. 60). Refresh de 1 día. |
| 4 | Permisos por rol con deny-by-default; no confiar en que el front oculte botones. | `torneo/permissions.py`: anónimo solo lectura (401 al escribir), planillero solo PATCH de `goles_local`, `goles_visita`, `estado` (403 en otro campo), administrador total. |
| 5 | Validar entradas del lado del servidor (reglas de negocio, filtros). | `serializers.py::validate` (local ≠ visita, misma liga), `models.py::clean`, `api_views.py` (filtros inválidos → 400). |
| 6 | Limitar peticiones (fuerza bruta y abuso). | `settings.py`: `DEFAULT_THROTTLE_RATES` (anon, user y scope `login` 30/min en `/api/token/`). |
| 7 | Evitar exponer datos innecesarios: serializers con lista explícita de campos. | `serializers.py` (`fields = [...]`, nunca `__all__`). `/api/me/` solo devuelve id, username y rol. |
| 8 | Endurecer cookies y cabeceras. | `settings.py`: `SESSION_COOKIE_HTTPONLY`, `SECURE_CONTENT_TYPE_NOSNIFF`; con `DEBUG=0`: cookies `Secure`, redirección SSL y HSTS. CSRF activo en todos los formularios HTML. |
| 9 | Contraseñas fuertes y sin credenciales en el repositorio. | `AUTH_PASSWORD_VALIDATORS` activos. El comando `seed` es solo para desarrollo y no se usa en producción. |
| 10 | Token en `sessionStorage` en el front (no `localStorage`). | Ya lo hace el front del profesor (`app.js`); sin cambios. |

## 4. Pendiente / fuera de alcance
- En producción: servir por HTTPS, definir `DJANGO_ALLOWED_HOSTS` y rotar la clave.
- Una blacklist de refresh tokens (`rest_framework_simplejwt.token_blacklist`) permitiría revocar sesiones; no se activó para mantener el proyecto simple.
