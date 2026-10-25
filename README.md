# Sistema Web de Votaciones – Festival de la Leyenda Vallenata 2027

Proyecto académico de la asignatura **Desarrollo Web** (Fundación Universitaria del Área Andina, Ingeniería de Sistemas).
Plataforma web configurable para gestionar las votaciones del público del Festival de la Leyenda Vallenata, construida con **Python, Django (patrón MVT) y MySQL**.

> Proyecto académico con datos de prueba. No es un sitio oficial del Festival ni de la Fundación.

- **Prototipo de la Entrega 1:** https://jang3l-98.github.io/votaciones-festival-2027/
- **Mapa de pantallas del prototipo:** https://jang3l-98.github.io/votaciones-festival-2027/mapa.html

## Equipo

| Integrante | Responsabilidad en la Entrega 2 |
| --- | --- |
| Juan Angel Velásquez Gómez | Proyecto Django, conexión a MySQL, modelos y migraciones, plantilla base, integración |
| Harold de Jesús Marimón Herrera | Registro, inicio y cierre de sesión |
| Liana Victoria Gaitán Higuera | Interfaz pública: categorías, votaciones y detalle |
| John Edisson Gómez Cortés | Django Admin, datos de prueba y pruebas |

## Qué hace esta versión (Entrega 2)

- Proyecto Django con dos aplicaciones: `cuentas` (usuarios) y `votaciones` (ediciones, categorías, votaciones y opciones).
- Datos guardados en **MySQL**, con modelos relacionados **Edición → Categoría → Votación → Opción**.
- Todo se configura desde **Django Admin**: no hay categorías ni votaciones escritas en el código.
- Registro, inicio y cierre de sesión con el sistema de usuarios de Django (contraseñas cifradas).
- Páginas públicas que leen los datos de MySQL con vistas y plantillas.

## Estructura del proyecto

```
votaciones-festival-2027/
├── config/                 Configuración del proyecto (settings.py, urls.py)
├── cuentas/                App de usuarios: modelo Usuario, inicio/cierre de sesión, registro
├── votaciones/             App principal: modelos, admin, vistas, rutas y pruebas
│   ├── models.py           Edicion, Categoria, Votacion, Opcion
│   ├── admin.py            Administración en Django Admin
│   ├── views.py            Vistas públicas (la «V» de MVT)
│   ├── urls.py             Rutas públicas
│   └── tests.py            Pruebas automáticas
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
python manage.py migrate          # crea las tablas en MySQL
python manage.py createsuperuser  # usuario para entrar a /admin
python manage.py cargar_datos_prueba   # edición 2027 con categorías, votaciones y opciones de prueba
python manage.py runserver
```

- Sitio público: http://127.0.0.1:8000/
- Administración: http://127.0.0.1:8000/admin/

### Pruebas automáticas

```bash
python manage.py test
```

## Modelo de datos

| Modelo | Qué representa | Relación |
| --- | --- | --- |
| `Edicion` | Una edición anual del Festival (por ejemplo, 2027, edición 60). Solo una está activa. | Tiene muchas categorías |
| `Categoria` | Un grupo de votaciones (Música, Piloneras…) | Pertenece a una edición |
| `Votacion` | Una votación del público, con fechas de apertura y cierre y reglas configurables | Pertenece a una categoría |
| `Opcion` | Lo que el público puede elegir (canción, artista, comparsa…) | Pertenece a una votación |
| `Usuario` | Persona registrada; ingresa con su correo | Votará en la siguiente entrega |

Las reglas que la Fundación aún no define (votos por usuario, publicación de resultados, votación de prueba) son campos de cada votación, para que se configuren sin cambiar el código.

## Convenciones

- Trabaja en una rama propia y pide la integración con un *pull request* (ver `CONTRIBUTING.md`).
- Nunca subas `.env`, contraseñas ni la base de datos.
- Colores y tipografías: `static/css/estilos.css`, bloque `:root`.
- Plantillas: todas extienden `templates/base.html`.

## Tecnologías

Python 3.12 · Django 5.2 · MySQL 8 · HTML5 · CSS3 · Bootstrap 5.3 · JavaScript
