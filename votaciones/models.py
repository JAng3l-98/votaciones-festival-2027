"""
Modelos del sistema de votaciones: Edición → Categoría → Votación → Opción, y el Voto.

Todo es configurable desde la administración: no hay categorías, votaciones ni reglas
fijas en el código. La regla central de la Entrega 3 (un voto por usuario, categoría y
edición) es la regla por defecto de cada categoría; el administrador puede cambiarla por
«un voto en cada votación de la categoría». La base de datos garantiza la regla elegida
con una restricción única en el modelo Voto.
"""
import secrets

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F, Q
from django.urls import reverse
from django.utils import timezone


class Fechas(models.Model):
    """Fechas de creación y última modificación, comunes a todos los modelos."""
    creado = models.DateTimeField("creado", auto_now_add=True)
    actualizado = models.DateTimeField("actualizado", auto_now=True)

    class Meta:
        abstract = True


# ---------------------------------------------------------------- Edición
class EdicionQuerySet(models.QuerySet):
    def activa(self):
        """La edición que ve el público: la marcada como activa o, si no hay, la más reciente."""
        return self.filter(activa=True).first() or self.order_by("-anio").first()


class Edicion(Fechas):
    """Una edición anual del Festival, por ejemplo «Festival 2027», edición número 60."""
    nombre = models.CharField("nombre", max_length=120)
    anio = models.PositiveSmallIntegerField("año", unique=True)
    numero = models.PositiveSmallIntegerField("número de edición", null=True, blank=True)
    fecha_inicio = models.DateField("fecha de inicio", null=True, blank=True)
    fecha_fin = models.DateField("fecha de fin", null=True, blank=True)
    descripcion = models.TextField("descripción", blank=True)
    activa = models.BooleanField(
        "edición activa", default=False,
        help_text="Es la edición que ve el público. Al activar una, las demás se desactivan.")

    objects = EdicionQuerySet.as_manager()

    class Meta:
        verbose_name = "edición"
        verbose_name_plural = "ediciones"
        ordering = ["-anio"]
        constraints = [
            models.CheckConstraint(
                condition=Q(fecha_inicio__isnull=True) | Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=F("fecha_inicio")),
                name="edicion_fin_despues_de_inicio",
                violation_error_message="La fecha de fin no puede ser anterior a la fecha de inicio.",
            ),
        ]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        # Solo una edición activa a la vez (MySQL no admite restricciones únicas condicionales).
        with transaction.atomic():
            if self.activa:
                Edicion.objects.filter(activa=True).exclude(pk=self.pk).update(activa=False)
            super().save(*args, **kwargs)


# ---------------------------------------------------------------- Categoría
class Categoria(Fechas):
    """Agrupa votaciones dentro de una edición: Música, Desfile y comparsas, Piloneras…"""

    class ReglaVoto(models.TextChoices):
        # Regla de la guía de la Entrega 3: una sola opción en toda la categoría, aunque tenga
        # varias votaciones (subeventos). Es la regla por defecto.
        UNO_POR_CATEGORIA = "categoria", "Un solo voto en toda la categoría"
        # Regla alternativa configurable: un voto en cada votación de la categoría.
        UNO_POR_VOTACION = "votacion", "Un voto en cada votación de la categoría"

    edicion = models.ForeignKey(Edicion, on_delete=models.PROTECT, related_name="categorias", verbose_name="edición")
    nombre = models.CharField("nombre", max_length=120)
    slug = models.SlugField("identificador en la URL", max_length=140)
    descripcion = models.TextField("descripción", blank=True)
    orden = models.PositiveSmallIntegerField("orden en el sitio", default=0)
    visible = models.BooleanField("visible para el público", default=True)
    regla_voto = models.CharField(
        "regla de votos", max_length=12, choices=ReglaVoto.choices, default=ReglaVoto.UNO_POR_CATEGORIA,
        help_text="Un solo voto en toda la categoría (regla de la Entrega 3) o un voto en cada una de sus votaciones. "
                  "No se puede cambiar cuando la categoría ya tiene votos.")

    class Meta:
        verbose_name = "categoría"
        verbose_name_plural = "categorías"
        ordering = ["edicion", "orden", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["edicion", "slug"], name="categoria_slug_unico_por_edicion",
                                    violation_error_message="Ya existe una categoría con ese identificador en esta edición."),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.edicion.anio})"

    @property
    def un_voto_por_categoria(self):
        return self.regla_voto == self.ReglaVoto.UNO_POR_CATEGORIA

    def clean(self):
        # Cambiar la regla con votos ya registrados dejaría votos que no la cumplen.
        if self.pk:
            anterior = Categoria.objects.filter(pk=self.pk).values_list("regla_voto", flat=True).first()
            if anterior and anterior != self.regla_voto and self.votos.exists():
                raise ValidationError({"regla_voto": "Esta categoría ya tiene votos: su regla de votos no se puede cambiar."})


# ---------------------------------------------------------------- Votación
class VotacionQuerySet(models.QuerySet):
    def visibles(self):
        return self.filter(visible=True, categoria__visible=True)

    def de_edicion(self, edicion):
        return self.filter(categoria__edicion=edicion)

    def abiertas(self):
        ahora = timezone.now()
        return self.filter(fecha_apertura__lte=ahora, fecha_cierre__gt=ahora)

    def proximas(self):
        return self.filter(fecha_apertura__gt=timezone.now())

    def cerradas(self):
        return self.filter(fecha_cierre__lte=timezone.now())


class Votacion(Fechas):
    """Una votación del público dentro de una categoría, con sus fechas y reglas configurables."""

    class Estado(models.TextChoices):
        PROXIMA = "proxima", "Próximamente"
        ABIERTA = "abierta", "Abierta"
        CERRADA = "cerrada", "Cerrada"

    class Publicacion(models.TextChoices):
        AL_CIERRE = "al_cierre", "Al cierre de la votación"
        EN_VIVO = "en_vivo", "En vivo"
        NO_PUBLICAR = "no_publicar", "No publicar"

    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="votaciones", verbose_name="categoría")
    nombre = models.CharField("nombre", max_length=160)
    slug = models.SlugField("identificador en la URL", max_length=180)
    descripcion = models.TextField("descripción", blank=True)
    imagen = models.ImageField("imagen", upload_to="votaciones/", blank=True)
    fecha_apertura = models.DateTimeField("abre")
    fecha_cierre = models.DateTimeField("cierra")
    # Reglas configurables por votación (pendientes de validación con la Fundación).
    # El número de votos ya no es configurable: la Entrega 3 fija un voto por categoría (ver Voto).
    publicacion_resultados = models.CharField(
        "publicación de resultados", max_length=20, choices=Publicacion.choices, default=Publicacion.AL_CIERRE)
    es_prueba = models.BooleanField(
        "votación de prueba", default=False,
        help_text="Sirve para ensayar antes de la votación real; sus votos no cuentan en los resultados (RF-13).")
    visible = models.BooleanField("visible para el público", default=True)
    orden = models.PositiveSmallIntegerField("orden en el sitio", default=0)

    objects = VotacionQuerySet.as_manager()

    class Meta:
        verbose_name = "votación"
        verbose_name_plural = "votaciones"
        ordering = ["categoria", "orden", "fecha_apertura"]
        constraints = [
            models.UniqueConstraint(fields=["categoria", "slug"], name="votacion_slug_unico_por_categoria",
                                    violation_error_message="Ya existe una votación con ese identificador en esta categoría."),
            models.CheckConstraint(condition=Q(fecha_cierre__gt=F("fecha_apertura")), name="votacion_cierre_despues_de_apertura",
                                   violation_error_message="La fecha de cierre debe ser posterior a la de apertura."),
        ]

    def __str__(self):
        return self.nombre

    @property
    def edicion(self):
        return self.categoria.edicion

    @property
    def estado(self):
        ahora = timezone.now()
        if ahora < self.fecha_apertura:
            return self.Estado.PROXIMA
        if ahora < self.fecha_cierre:
            return self.Estado.ABIERTA
        return self.Estado.CERRADA

    def get_estado_display(self):
        return self.Estado(self.estado).label

    def get_absolute_url(self):
        return reverse("votaciones:detalle", args=[self.pk])


# ---------------------------------------------------------------- Opción
class Opcion(Fechas):
    """Lo que el público puede elegir en una votación: una canción, un artista, una comparsa…"""
    votacion = models.ForeignKey(Votacion, on_delete=models.PROTECT, related_name="opciones", verbose_name="votación")
    nombre = models.CharField("nombre", max_length=160)
    descripcion = models.CharField("descripción", max_length=255, blank=True)
    imagen = models.ImageField("imagen", upload_to="opciones/", blank=True)
    orden = models.PositiveSmallIntegerField("orden", default=0)
    activa = models.BooleanField("activa", default=True)

    class Meta:
        verbose_name = "opción"
        verbose_name_plural = "opciones"
        ordering = ["votacion", "orden", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["votacion", "nombre"], name="opcion_nombre_unico_por_votacion",
                                    violation_error_message="Esta votación ya tiene una opción con ese nombre."),
        ]

    def __str__(self):
        return self.nombre


# ---------------------------------------------------------------- Voto
ALFABETO_COMPROBANTE = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"   # sin 0, O, 1 ni I, que se confunden


def nuevo_comprobante(anio):
    """Código que el usuario guarda como constancia de su voto, por ejemplo «VF27-4K9P-2QXM»."""
    cuerpo = "".join(secrets.choice(ALFABETO_COMPROBANTE) for _ in range(8))
    return f"VF{anio % 100:02d}-{cuerpo[:4]}-{cuerpo[4:]}"


class Voto(models.Model):
    """
    El voto de un usuario. Regla central de la Entrega 3: una sola opción por usuario,
    categoría y edición. Se puede votar en otras categorías, pero no dos veces en la
    misma, aunque la categoría tenga varias votaciones (subeventos). Si el administrador
    configura la categoría con «un voto en cada votación», el límite pasa a ser uno por votación.
    """
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="votos", verbose_name="usuario")
    # La edición y la categoría se guardan también en el voto para que MySQL pueda exigir
    # la restricción única: una restricción no puede consultar otras tablas.
    edicion = models.ForeignKey(Edicion, on_delete=models.PROTECT, related_name="votos", verbose_name="edición")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="votos", verbose_name="categoría")
    votacion = models.ForeignKey(Votacion, on_delete=models.PROTECT, related_name="votos", verbose_name="votación")
    opcion = models.ForeignKey(Opcion, on_delete=models.PROTECT, related_name="votos", verbose_name="opción")
    # Alcance de la regla de la categoría: 0 cuando el voto ocupa toda la categoría (regla por
    # defecto) o el id de la votación cuando la categoría permite un voto en cada votación.
    alcance = models.PositiveBigIntegerField("alcance de la regla", default=0, editable=False)
    comprobante = models.CharField("comprobante", max_length=16, unique=True, editable=False)
    fecha = models.DateTimeField("fecha del voto", auto_now_add=True)

    class Meta:
        verbose_name = "voto"
        verbose_name_plural = "votos"
        ordering = ["-fecha"]
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "edicion", "categoria", "alcance"], name="voto_unico_usuario_categoria_edicion",
                violation_error_message="Este usuario ya votó en esta categoría de la edición."),
        ]

    def __str__(self):
        return f"{self.usuario} · {self.categoria.nombre}: {self.opcion}"

    def save(self, *args, **kwargs):
        # La votación, la categoría y la edición se toman de la opción elegida:
        # así un voto nunca puede quedar con datos que no coinciden entre sí.
        self.votacion = self.opcion.votacion
        self.categoria = self.votacion.categoria
        self.edicion = self.categoria.edicion
        # Con la regla por defecto todos los votos de la categoría tienen alcance 0, así que la
        # restricción única deja uno solo por usuario, categoría y edición.
        self.alcance = 0 if self.categoria.un_voto_por_categoria else self.votacion_id
        if not self.comprobante:
            self.comprobante = nuevo_comprobante(self.edicion.anio)
        super().save(*args, **kwargs)
