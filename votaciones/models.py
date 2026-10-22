"""
Modelos del sistema de votaciones: Edición → Categoría → Votación → Opción.

Todo es configurable desde la administración: no hay categorías, votaciones ni reglas
fijas en el código. Las reglas que la Fundación aún no define (votos por persona,
publicación de resultados) son campos de cada votación.
"""
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
    edicion = models.ForeignKey(Edicion, on_delete=models.PROTECT, related_name="categorias", verbose_name="edición")
    nombre = models.CharField("nombre", max_length=120)
    slug = models.SlugField("identificador en la URL", max_length=140)
    descripcion = models.TextField("descripción", blank=True)
    orden = models.PositiveSmallIntegerField("orden en el sitio", default=0)
    visible = models.BooleanField("visible para el público", default=True)

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
    # Reglas configurables por votación (pendientes de validación con la Fundación)
    votos_por_usuario = models.PositiveSmallIntegerField(
        "votos por usuario", default=1,
        help_text="Cuántas veces puede votar cada usuario en esta votación (regla configurable).")
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
            models.CheckConstraint(condition=Q(votos_por_usuario__gte=1), name="votacion_al_menos_un_voto",
                                   violation_error_message="Cada usuario debe poder votar al menos una vez."),
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
