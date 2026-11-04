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
| Entrega 3 – Módulo de votaciones, validaciones y API GET | `main` (la etiqueta `entrega-3` se crea al entregar) |

## Equipo

| Integrante | Entrega 2 | Entrega 3 |
| --- | --- | --- |
| Juan Angel Velásquez Gómez | Proyecto Django, conexión a MySQL, modelos y migraciones, plantilla base, integración | Modelo `Voto`, validaciones del servidor, restricción única, concurrencia, API GET, integración |
| Harold de Jesús Marimón Herrera | Registro, inicio y cierre de sesión | Autenticación para votar y página «Mis votos» (participación) |
| Liana Victoria Gaitán Higuera | Interfaz pública: categorías, votaciones y detalle | Pantallas del proceso de votación: elegir, confirmar y comprobante |
| John Edisson Gómez Cortés | Django Admin, datos de prueba y pruebas | Consulta administrativa de votos y verificación contra MySQL |

## Qué hace esta versión (Entrega 3)

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
├── cuentas/                App de usuarios: modelo Usuario, inicio/cierre de sesión, registro
├── votaciones/             App principal: modelos, admin, vistas, rutas y pruebas
│   ├── models.py           Edicion, Categoria, Votacion, Opcion y Voto (restricción única)
│   ├── servicios.py        Reglas y validaciones del voto (Entrega 3)
│   ├── api.py              API GET /api/categorias/ (Entrega 3)
│   ├── admin.py            Administración en Django Admin
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
python manage.py migrate          # crea las tablas en MySQL (en la Entrega 3 agrega la tabla de votos)
python manage.py createsuperuser  # usuario para entrar a /admin
python manage.py cargar_datos_prueba   # edición 2027 con categorías, votaciones y opciones de prueba
python manage.py runserver
```

- Sitio público: http://127.0.0.1:8000/
- Administración: http://127.0.0.1:8000/admin/
- API GET: http://127.0.0.1:8000/api/categorias/

Para votar, crea una cuenta en «Crear cuenta» (o usa la del administrador), entra a una votación abierta, elige una opción y confírmala.

> Si ya tenías el proyecto de la Entrega 2: `git pull`, `python manage.py migrate` y `python manage.py cargar_datos_prueba`. La migración `0002` crea la tabla de votos y retira el campo «votos por usuario» de cada votación; la `0003` agrega la regla de votos configurable en cada categoría.

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
```

## Modelo de datos

| Modelo | Qué representa | Relación |
| --- | --- | --- |
| `Edicion` | Una edición anual del Festival (por ejemplo, 2027, edición 60). Solo una está activa. | Tiene muchas categorías |
| `Categoria` | Un grupo de votaciones (Música, Piloneras…), con su regla de votos | Pertenece a una edición |
| `Votacion` | Una votación del público, con fechas de apertura y cierre y reglas configurables | Pertenece a una categoría |
| `Opcion` | Lo que el público puede elegir (canción, artista, comparsa…) | Pertenece a una votación |
| `Usuario` | Persona registrada; ingresa con su correo | Tiene muchos votos |
| `Voto` | La opción que eligió un usuario, con fecha y comprobante | Pertenece a un usuario, una edición, una categoría, una votación y una opción. **Único por usuario, categoría y edición** (o por votación, si la categoría lo permite) |

Las reglas que la Fundación aún no define (publicación de resultados, votación de prueba) son campos de cada votación, para que se configuren sin cambiar el código. La regla de votos es un campo de cada categoría: por defecto, un solo voto en toda la categoría, como pide la Entrega 3.

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

## Convenciones

- Trabaja en una rama propia y pide la integración con un *pull request* (ver `CONTRIBUTING.md`).
- Nunca subas `.env`, contraseñas ni la base de datos.
- Colores y tipografías: `static/css/estilos.css`, bloque `:root`.
- Plantillas: todas extienden `templates/base.html`.

## Tecnologías

Python 3.12 · Django 5.2 · MySQL 8 · HTML5 · CSS3 · Bootstrap 5.3 · JavaScript
