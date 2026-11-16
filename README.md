# Sistema Web de Votaciones – Festival de la Leyenda Vallenata 2027

Proyecto académico de la asignatura **Desarrollo Web** (Fundación Universitaria del Área Andina, Ingeniería de Sistemas).
Plataforma web configurable para gestionar las votaciones del público del Festival de la Leyenda Vallenata, construida con **Python, Django (patrón MVT) y MySQL**.

> Proyecto académico con datos de prueba. No es un sitio oficial del Festival ni de la Fundación.

- **Prototipo de la Entrega 1:** https://jang3l-98.github.io/votaciones-festival-2027/
- **Mapa de pantallas del prototipo:** https://jang3l-98.github.io/votaciones-festival-2027/mapa.html

## Versiones entregadas

Cada entrega queda guardada con una etiqueta (*tag*) de Git, para revisar el código tal como se entregó aunque el proyecto siga avanzando en `main`:

| Entrega | Versión |
| --- | --- |
| Entrega 1 – Prototipo UX/UI y documentación | [entrega-1](https://github.com/JAng3l-98/votaciones-festival-2027/tree/entrega-1) |
| Entrega 2 – Desarrollo inicial del sistema de votaciones | [entrega-2](https://github.com/JAng3l-98/votaciones-festival-2027/tree/entrega-2) |
| Entrega 3 – Módulo de votaciones, validaciones y API GET | [entrega-3](https://github.com/JAng3l-98/votaciones-festival-2027/tree/entrega-3) |
| Entrega final – Sustentación del sistema | `main` |

## Equipo

| Integrante | Entrega 2 | Entrega 3 |
| --- | --- | --- |
| Juan Angel Velásquez Gómez | Proyecto Django, conexión a MySQL, modelos y migraciones, plantilla base, integración | Modelo `Voto`, validaciones del servidor, restricción única, concurrencia, API GET, integración |
| Harold de Jesús Marimón Herrera | Registro, inicio y cierre de sesión | Autenticación para votar y página «Mis votos» (participación) |
| Liana Victoria Gaitán Higuera | Interfaz pública: categorías, votaciones y detalle | Pantallas del proceso de votación: elegir, confirmar y comprobante |
| John Edisson Gómez Cortés | Django Admin, datos de prueba y pruebas | Consulta administrativa de votos y verificación contra MySQL |

## Qué agrega la entrega final

- **Resultados con datos reales** (`/resultados/`): votos por opción, porcentaje y quién va ganando (o el empate), contados en MySQL al abrir la página. Cada votación define en la administración **cuándo** se publican (en vivo, al cierre o nunca) y **a quiénes** se muestran (todo el público o solo usuarios registrados). La administración los ve siempre como **vista previa** y puede descargarlos en CSV. Las votaciones de prueba nunca publican resultados.
- **Permisos diferenciados:** votantes (sin acceso a la administración), grupo **«Administración del Festival»** (configura ediciones, categorías, votaciones y opciones; los votos solo los consulta) y superusuario (además gestiona usuarios y grupos). `migrate` crea el grupo con sus permisos.
- **Los votos no se modifican ni se borran desde la administración**, ni siquiera el superusuario. Tampoco se puede mover a otro lugar lo que ya tiene votos (una opción a otra votación, una votación a otra categoría, una categoría a otra edición), y la base de datos impide borrar opciones, votaciones o categorías con votos (`on_delete=PROTECT`).
- **Nueva edición sin tocar el código:** acción «Duplicar para el año siguiente» en Ediciones (copia categorías, votaciones y opciones con las fechas corridas un año, sin votos, y la deja inactiva) y acción «Marcar como la edición activa».
- **Recuperar y cambiar la contraseña:** enlace «¿Olvidaste tu contraseña?» en el ingreso; el enlace llega por correo, vence en una hora y sirve una sola vez. Con sesión iniciada, «Cambiar contraseña» en el pie de página.
- **Listo para publicarse:** configuración de HTTPS con una variable de entorno, páginas de error propias (404, 403, 500 y formulario caducado) y `check --deploy` sin advertencias.
- **Votos de prueba:** `cargar_votos_prueba` registra votos de votantes ficticios para que los resultados tengan datos.

## Lo que ya venía de la Entrega 3

- **Módulo de votaciones:** el usuario inicia sesión, elige una categoría y una opción, confirma y el voto se guarda en MySQL con un comprobante.
- **Regla central:** cada usuario elige **una sola opción por categoría y edición**. Puede votar en otras categorías, pero no dos veces en la misma, aunque tenga varias votaciones (subeventos). Es la regla por defecto de cada categoría.
- **Regla configurable:** en Django Admin, cada categoría puede cambiarse a «Un voto en cada votación de la categoría» (por ejemplo, si la Fundación decide que en una categoría se vota en cada subevento). La regla no se puede cambiar cuando la categoría ya tiene votos.
- **Validaciones en el servidor** (`votaciones/servicios.py`): sesión iniciada, votación visible y abierta, edición activa, opción que pertenece a la votación y voto no repetido. Los formularios usan **POST** con **token CSRF**.
- **Integridad en la base de datos:** restricción única `voto_unico_usuario_categoria_edicion` sobre (usuario, edición, categoría, alcance) en el modelo `Voto` (`votaciones/models.py`). Con la regla por defecto el alcance siempre es 0, así que queda un solo voto por usuario, categoría y edición; con la regla «un voto en cada votación», el alcance es la votación. Si llegan dos solicitudes al mismo tiempo, MySQL deja guardar solo una.
- **Participación:** cada usuario consulta sus votos; el administrador consulta todos los votos en Django Admin.
- **API GET** `/api/categorias/` (`votaciones/api.py`): categorías de la edición activa con sus votaciones y opciones, en JSON, leídas de MySQL.

Versiones anteriores: la Entrega 2 creó el proyecto, los modelos Edición → Categoría → Votación → Opción, Django Admin, el registro de usuarios y las páginas públicas.

## Estructura del proyecto

```
votaciones-festival-2027/
├── config/                 Configuración del proyecto (settings.py, urls.py)
├── cuentas/                App de usuarios: modelo Usuario, ingreso, registro y contraseñas
├── votaciones/             App principal: modelos, admin, vistas, rutas y pruebas
│   ├── models.py           Edicion, Categoria, Votacion, Opcion y Voto (restricción única)
│   ├── servicios.py        Reglas y validaciones del voto (Entrega 3)
│   ├── resultados.py       Cuándo y a quiénes se muestran los resultados, y su conteo (entrega final)
│   ├── permisos.py         Grupo «Administración del Festival» (entrega final)
│   ├── ediciones.py        Duplicar una edición para el año siguiente (entrega final)
│   ├── api.py              API GET /api/categorias/ (Entrega 3)
│   ├── admin.py            Administración en Django Admin
│   ├── management/commands cargar_datos_prueba, cargar_votos_prueba y probar_concurrencia
│   ├── views.py            Vistas públicas y proceso de votación (la «V» de MVT)
│   ├── urls.py             Rutas públicas y de la API
│   └── test_*.py           Pruebas automáticas
├── templates/              Plantillas HTML (la «T» de MVT); base.html tiene el encabezado y el pie
├── static/                 CSS, JavaScript, tipografías e imágenes (identidad del prototipo)
├── docs/                   Prototipo navegable de la Entrega 1 (lo publica GitHub Pages)
├── manage.py
├── requirements.txt        Librerías de Python
├── .env.example            Plantilla de variables de entorno (copiar como .env)
├── CONTRIBUTING.md         Cómo trabajar en equipo con Git y GitHub
└── README.md
```

## Instalación

Necesitas **Git**, **Python 3.12** (sirve de 3.10 a 3.13), **MySQL 8** y **Visual Studio Code**.

### macOS

```bash
# 1. Programas (con Homebrew)
brew install python@3.12 mysql pkg-config
brew services start mysql

# 2. Base de datos y usuario de MySQL (ver «Crear la base de datos» más abajo)
mysql -u root

# 3. Proyecto
git clone https://github.com/JAng3l-98/votaciones-festival-2027.git
cd votaciones-festival-2027
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # y luego edita .env con tus datos
```

### Windows

1. Instala **Python 3.12** desde https://www.python.org/downloads/ y marca **«Add python.exe to PATH»**.
2. Instala **MySQL Community Server 8** con el *MySQL Installer* (https://dev.mysql.com/downloads/installer/). Elige *Server only* y anota la contraseña de `root`.
3. Abre **MySQL 8.0 Command Line Client**, escribe la contraseña de `root` y crea la base de datos (siguiente sección).
4. En la terminal de VS Code (PowerShell):

```powershell
git clone https://github.com/JAng3l-98/votaciones-festival-2027.git
cd votaciones-festival-2027
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env        # y luego edita .env con tus datos
```

> Si PowerShell no deja activar el entorno, ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

### Crear la base de datos

Dentro de la consola de MySQL (cambia `tu-clave` por una clave tuya):

```sql
CREATE DATABASE votaciones_festival CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'festival'@'localhost' IDENTIFIED BY 'tu-clave';
GRANT ALL PRIVILEGES ON votaciones_festival.* TO 'festival'@'localhost';
GRANT ALL PRIVILEGES ON test_votaciones_festival.* TO 'festival'@'localhost';  -- para las pruebas automáticas
FLUSH PRIVILEGES;
EXIT;
```

### Configurar el archivo `.env`

Abre `.env` y completa:

- `DJANGO_SECRET_KEY`: genera una clave con
  `python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"`
- `DB_PASSWORD`: la clave que pusiste al usuario `festival`.

El archivo `.env` **no se sube a GitHub**: cada integrante tiene el suyo.

### Ejecutar

```bash
python manage.py migrate               # crea las tablas en MySQL y el grupo «Administración del Festival»
python manage.py createsuperuser       # usuario para entrar a /admin
python manage.py cargar_datos_prueba   # edición 2027 con categorías, votaciones y opciones de prueba
python manage.py cargar_votos_prueba   # votos de 40 votantes ficticios, para ver resultados
python manage.py runserver
```

- Sitio público: http://127.0.0.1:8000/
- Resultados: http://127.0.0.1:8000/resultados/
- Administración: http://127.0.0.1:8000/admin/
- API GET: http://127.0.0.1:8000/api/categorias/

Para votar, crea una cuenta en «Crear cuenta» (o usa la del administrador), entra a una votación abierta, elige una opción y confírmala.

> Si ya tenías el proyecto: `git pull`, `python manage.py migrate` y `python manage.py cargar_datos_prueba`. La migración `0002` crea la tabla de votos; la `0003` agrega la regla de votos configurable en cada categoría; la `0004` agrega «quién ve los resultados» en cada votación.

### Roles y permisos

| Rol | Cómo se crea | Qué puede hacer |
| --- | --- | --- |
| Votante | «Crear cuenta» en el sitio | Votar, ver sus votos y los resultados publicados. No entra a la administración. |
| Administración del Festival | En `/admin/` → Usuarios: marcar «Es staff» y agregarlo al grupo «Administración del Festival» | Configurar ediciones, categorías, votaciones y opciones; consultar votos y ver resultados antes de publicarse. No modifica ni borra votos. |
| Superusuario | `python manage.py createsuperuser` | Todo lo anterior, más usuarios y grupos. Tampoco modifica ni borra votos. |

### Resultados

En la administración, cada votación tiene la sección **Resultados**:

- **Publicación de resultados** (cuándo): *En vivo* (mientras está abierta), *Al cierre de la votación* o *No publicar*.
- **Quién ve los resultados** (a quiénes): *Todo el público* o *Solo usuarios registrados*.

Los resultados se cuentan en MySQL cada vez que se abre la página. La administración los ve siempre (como «vista previa» mientras no estén publicados) y los descarga en CSV desde la página de resultados.

### Recuperar la contraseña

En el ingreso, «¿Olvidaste tu contraseña?» pide el correo y envía un enlace. En el equipo local **el correo se muestra en la terminal donde corre `runserver`**: copia el enlace de ahí y ábrelo en el navegador. Para enviar correos reales se configuran las variables `EMAIL_*` del `.env` (ver `.env.example`).

### Votos de prueba

```bash
python manage.py cargar_votos_prueba                          # 40 votantes ficticios
python manage.py cargar_votos_prueba --votantes 80 --semilla 7
```

Crea votantes `votante01@ejemplo.com`, `votante02@ejemplo.com`… sin contraseña utilizable (nadie puede ingresar con ellos) y les registra votos en las votaciones que ya abrieron, respetando la regla de cada categoría. Se puede ejecutar varias veces: quien ya votó en una categoría no vuelve a votar. No toca los votos de los usuarios reales.

### Probar la concurrencia (CP-09)

Envía al mismo tiempo varias solicitudes de voto del mismo usuario a una categoría y muestra cuántos votos quedan en MySQL (debe quedar uno):

```bash
python manage.py probar_concurrencia correo-de-un-usuario@ejemplo.com
python manage.py probar_concurrencia correo-de-un-usuario@ejemplo.com --solicitudes 5
```

El voto que queda registrado es real: usa un usuario de prueba.

### Pruebas automáticas

```bash
python manage.py test                              # todas
python manage.py test votaciones.test_votos -v 2   # casos CP-01 a CP-10 del módulo de votos
python manage.py test votaciones.test_resultados   # resultados: cuándo, a quiénes y conteo
```

## Publicar el sitio para usuarios externos

El proyecto se entrega para ejecutarse en un equipo local. Para publicarlo en internet hacen falta, además del código:

1. **Un servidor con MySQL 8** y un dominio propio, con **certificado HTTPS** (por ejemplo, de Let's Encrypt).
2. **Variables de entorno de producción** en el `.env` del servidor: `DJANGO_DEBUG=False`, una `DJANGO_SECRET_KEY` nueva, `DJANGO_ALLOWED_HOSTS` y `DJANGO_CSRF_TRUSTED_ORIGINS` con el dominio, y `DJANGO_HTTPS=1` (redirige a HTTPS, cookies seguras y HSTS). Con eso, `python manage.py check --deploy` no muestra advertencias.
3. **Un servidor de aplicaciones** (Gunicorn) detrás de **Nginx**, que además sirve los archivos estáticos reunidos con `python manage.py collectstatic` y las imágenes de `media/`.
4. **Un servidor de correo (SMTP)** en las variables `EMAIL_*`, para que lleguen los enlaces de recuperar la contraseña.
5. **Copias de seguridad** periódicas de la base de datos (`mysqldump`) y un usuario de MySQL con permisos solo sobre esta base.
6. **Antes de abrir al público:** cambiar los datos de prueba por los reales, revisar con la Fundación la política de tratamiento de datos (Ley 1581 de 2012), el texto de autorización y los límites de intentos de ingreso, y hacer una prueba de carga con el número de votantes esperado.

## Modelo de datos

| Modelo | Qué representa | Relación |
| --- | --- | --- |
| `Edicion` | Una edición anual del Festival (por ejemplo, 2027, edición 60). Solo una está activa. | Tiene muchas categorías |
| `Categoria` | Un grupo de votaciones (Música, Piloneras…), con su regla de votos | Pertenece a una edición |
| `Votacion` | Una votación del público, con fechas de apertura y cierre, y cuándo y a quiénes se publican sus resultados | Pertenece a una categoría |
| `Opcion` | Lo que el público puede elegir (canción, artista, comparsa…) | Pertenece a una votación |
| `Usuario` | Persona registrada; ingresa con su correo | Tiene muchos votos |
| `Voto` | La opción que eligió un usuario, con fecha y comprobante | Pertenece a un usuario, una edición, una categoría, una votación y una opción. **Único por usuario, categoría y edición** (o por votación, si la categoría lo permite) |

Las reglas que decide la Fundación son campos que se configuran en la administración sin cambiar el código: en cada votación, cuándo y a quiénes se publican los resultados y si es una votación de prueba; en cada categoría, la regla de votos (por defecto, un solo voto en toda la categoría).

## API GET

`GET /api/categorias/` responde en JSON con la edición activa, sus categorías visibles (con su regla de votos), las votaciones de cada categoría y sus opciones activas. Con `?edicion=2026` consulta otra edición por su año. Es de solo lectura (cualquier otro método responde 405) y no entrega datos de usuarios ni de votos.

```json
{
  "edicion": {"id": 1, "nombre": "Festival de la Leyenda Vallenata 2027", "anio": 2027, "numero": 60},
  "total_categorias": 4,
  "categorias": [
    {
      "id": 1, "nombre": "Música", "slug": "musica", "descripcion": "…", "regla_voto": "categoria", "total_opciones": 7,
      "votaciones": [
        {"id": 1, "nombre": "Canción favorita del público", "estado": "abierta",
         "abre": "2026-10-01T13:00:00+00:00", "cierra": "2027-05-01T04:59:00+00:00",
         "url": "http://127.0.0.1:8000/votaciones/1/",
         "opciones": [{"id": 1, "nombre": "Brisa del Valle", "descripcion": "Dato de prueba.", "orden": 1}]}
      ]
    }
  ]
}
```

## Dónde está cada regla

| Regla | Archivo |
| --- | --- |
| Un voto por usuario, categoría y edición (base de datos) | `votaciones/models.py`, clase `Voto`, campo `alcance` y restricción `voto_unico_usuario_categoria_edicion`; migraciones `0002_voto_y_un_voto_por_categoria.py` y `0003_regla_de_votos_configurable.py` |
| Regla de votos configurable por categoría | `votaciones/models.py`, campo `Categoria.regla_voto` |
| Validaciones del voto y manejo del error de integridad | `votaciones/servicios.py` (`validar_voto` y `registrar_voto`) |
| Formularios POST con CSRF y sesión obligatoria | `votaciones/views.py` (`confirmar`, `votar`) |
| API GET | `votaciones/api.py` y ruta en `votaciones/urls.py` |
| Pruebas CP-01 a CP-10 | `votaciones/test_votos.py` |
| Cuándo y a quiénes se muestran los resultados, y su conteo | `votaciones/resultados.py`; vistas `resultados_lista`, `resultados` y `resultados_csv` en `votaciones/views.py` |
| Nadie modifica ni borra votos desde la administración | `votaciones/admin.py`, clase `VotoAdmin` |
| Lo que tiene votos no cambia de lugar | `votaciones/models.py`, métodos `clean()` de `Categoria`, `Votacion` y `Opcion`; campos de solo lectura en `votaciones/admin.py` |
| Grupo «Administración del Festival» | `votaciones/permisos.py` (se crea con `migrate`) |
| Duplicar una edición | `votaciones/ediciones.py` y acción en `EdicionAdmin` |
| Recuperar y cambiar la contraseña | `cuentas/urls.py` y plantillas `templates/cuentas/contrasena_*.html` |
| Configuración de producción (HTTPS, correo) | `config/settings.py` |
| Pruebas de la entrega final | `votaciones/test_resultados.py`, `votaciones/test_administracion_final.py`, `cuentas/test_contrasena.py` |

## Convenciones

- Trabaja en una rama propia y pide la integración con un *pull request* (ver `CONTRIBUTING.md`).
- Nunca subas `.env`, contraseñas ni la base de datos.
- Colores y tipografías: `static/css/estilos.css`, bloque `:root`.
- Plantillas: todas extienden `templates/base.html`.

## Tecnologías

Python 3.12 · Django 5.2 · MySQL 8 · HTML5 · CSS3 · Bootstrap 5.3 · JavaScript
