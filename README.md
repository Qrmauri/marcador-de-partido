# Marcador en Vivo

Aplicación de marcadores deportivos con Django, Django REST Framework y un frontend externo en HTML, CSS y JavaScript. Permite consultar ligas, equipos, jugadores, partidos y tablas de posiciones.

## Ejecutar en Windows

Desde la carpeta del proyecto:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed --password "TU_CLAVE_DE_DEMOSTRACION"
python manage.py runserver
```

El comando `seed` crea datos de ejemplo y los usuarios `admin`, `planillero` y `lector` con la contraseña indicada. Es para desarrollo local; al volver a ejecutarlo cambia las contraseñas de esos usuarios.

En otra terminal, desde la misma carpeta:

```powershell
python -m http.server 5500 --directory front_externo
```

Abre el frontend en <http://127.0.0.1:5500>. La API está en <http://127.0.0.1:8000/api/>. La dirección se configura en `front_externo/config.js`. Sirve el frontend por HTTP para que funcione la configuración de CORS.

## Roles

- Público y lector: consultar información.
- Planillero: actualizar goles y estado de partidos.
- Administrador: crear, modificar y eliminar recursos.

## API

| Método | Ruta | Función |
| --- | --- | --- |
| POST | `/api/token/` | Obtener access y refresh mediante usuario y contraseña |
| POST | `/api/token/refresh/` | Renovar access |
| GET | `/api/me/` | Consultar usuario y rol con JWT |
| GET | `/api/ligas/` | Listar ligas |
| GET | `/api/ligas/{id}/tabla/` | Consultar tabla de posiciones |
| GET | `/api/equipos/?liga={id}` | Consultar equipos de una liga |
| GET | `/api/jugadores/?equipo={id}` | Consultar jugadores de un equipo |
| GET | `/api/partidos/?liga={id}&estado=en_juego` | Filtrar partidos |
| PATCH | `/api/partidos/{id}/` | Actualizar un partido según el rol |

El frontend almacena los tokens en `sessionStorage` y envía access mediante `Authorization: Bearer <token>`. La tabla de posiciones se calcula con los partidos finalizados.

## Verificación

```powershell
python manage.py check
python manage.py test
```

## Configuración y material de presentación

Consulta `SEGURIDAD.md` para las medidas de seguridad y la configuración de producción. La configuración predeterminada es para desarrollo local.

El proyecto incluye el guion del video en `Guion_video_Marcador_en_Vivo.docx` y el diagrama en `diagrama_secuencia.png`.

La base de datos local y el entorno virtual no se incluyen en Git. Se recrean con la instalación de dependencias, las migraciones y el comando de datos de demostración.
