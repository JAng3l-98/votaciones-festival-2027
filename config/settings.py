"""
Configuración del proyecto Votaciones del Festival de la Leyenda Vallenata.

Los datos sensibles (clave secreta, usuario y contraseña de MySQL) NO se escriben aquí:
se leen del archivo .env, que cada integrante crea a partir de .env.example y que
Git no sube al repositorio.
"""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def variable(nombre, defecto=None, obligatoria=False):
    """Lee una variable del archivo .env (o del sistema)."""
    valor = os.environ.get(nombre, defecto)
    if obligatoria and not valor:
        raise ImproperlyConfigured(f"Falta la variable {nombre} en el archivo .env (copia .env.example).")
    return valor


def variable_booleana(nombre, defecto=False):
    return str(variable(nombre, str(defecto))).strip().lower() in ("1", "true", "si", "sí", "yes")


# ---------------------------------------------------------------- Seguridad
SECRET_KEY = variable("DJANGO_SECRET_KEY", obligatoria=True)
DEBUG = variable_booleana("DJANGO_DEBUG", False)
ALLOWED_HOSTS = [h.strip() for h in variable("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()]

# ---------------------------------------------------------------- Aplicaciones
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Aplicaciones del proyecto
    "cuentas",      # usuarios: registro, inicio y cierre de sesión
    "votaciones",   # ediciones, categorías, votaciones y opciones
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "votaciones.context_processors.edicion_activa",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------- Base de datos (MySQL)
# DB_ENGINE=mysql es lo normal. DB_ENGINE=sqlite solo sirve para correr las pruebas
# automáticas sin MySQL; la aplicación del proyecto trabaja sobre MySQL.
if variable("DB_ENGINE", "mysql") == "sqlite":
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": variable("DB_NAME", "votaciones_festival"),
            "USER": variable("DB_USER", obligatoria=True),
            "PASSWORD": variable("DB_PASSWORD", obligatoria=True),
            "HOST": variable("DB_HOST", "localhost"),
            "PORT": variable("DB_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",  # tildes, ñ y emojis
                "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }

# ---------------------------------------------------------------- Usuarios y autenticación
AUTH_USER_MODEL = "cuentas.Usuario"
LOGIN_URL = "cuentas:login"
LOGIN_REDIRECT_URL = "votaciones:inicio"
LOGOUT_REDIRECT_URL = "votaciones:inicio"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------- Idioma y hora de Colombia
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------- Archivos estáticos e imágenes
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
