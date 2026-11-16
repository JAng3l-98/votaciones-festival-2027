"""
Resultados de las votaciones (Entrega final). Los conteos se calculan en MySQL con Count
sobre la tabla de votos, al momento de abrir la página: no hay resultados guardados aparte.

Cada votación define en la administración:
  · CUÁNDO se publican (publicacion_resultados): en vivo, al cierre de la votación o nunca.
  · A QUIÉNES se muestran (audiencia_resultados): a todo el público o solo a usuarios registrados.
La administración (usuarios del equipo, is_staff) los ve siempre, como vista previa, para
revisarlos antes de que se publiquen.

Las votaciones de prueba no publican resultados: sus votos no cuentan (RF-13).
"""
from dataclasses import dataclass, field

from django.db.models import Count, Q
from django.utils.formats import date_format
from django.utils.timezone import localtime

from .models import Votacion


@dataclass
class Acceso:
    """Si un usuario puede ver los resultados de una votación y, si no, por qué."""
    permitido: bool
    vista_previa: bool = False     # la ve la administración, pero el público todavía no
    motivo: str = ""               # por qué el público no la ve (todavía)
    requiere_ingreso: bool = False  # se publica solo para usuarios registrados


@dataclass
class Fila:
    nombre: str
    descripcion: str
    votos: int
    porcentaje: float
    lider: bool = False


@dataclass
class Conteo:
    total: int
    filas: list = field(default_factory=list)
    lideres: list = field(default_factory=list)

    @property
    def empate(self):
        return len(self.lideres) > 1


def fecha_legible(fecha):
    return date_format(localtime(fecha), r"j \d\e F \d\e Y, g:i a").lower()


def regla_publicacion(votacion):
    """La regla de resultados en palabras, para mostrarla en el sitio."""
    if votacion.es_prueba or votacion.publicacion_resultados == Votacion.Publicacion.NO_PUBLICAR:
        return "no se publican; solo los consulta la administración"
    cuando = ("en vivo, mientras la votación está abierta"
              if votacion.publicacion_resultados == Votacion.Publicacion.EN_VIVO
              else f"al cierre de la votación ({fecha_legible(votacion.fecha_cierre)})")
    para = ("para todo el público" if votacion.audiencia_resultados == Votacion.Audiencia.PUBLICO
            else "solo para usuarios registrados")
    return f"se publican {cuando}, {para}"


def publicados(votacion):
    """(True, "") si el público ya puede ver los resultados; si no, (False, motivo)."""
    if votacion.es_prueba:
        return False, "Es una votación de prueba: sus votos no cuentan y sus resultados no se publican."
    if votacion.publicacion_resultados == Votacion.Publicacion.NO_PUBLICAR:
        return False, "Los resultados de esta votación no se publican."
    estado = votacion.estado
    if votacion.publicacion_resultados == Votacion.Publicacion.AL_CIERRE and estado != Votacion.Estado.CERRADA:
        return False, f"Los resultados se publican el {fecha_legible(votacion.fecha_cierre)}, al cierre de la votación."
    if estado == Votacion.Estado.PROXIMA:
        return False, f"La votación abre el {fecha_legible(votacion.fecha_apertura)}; los resultados se verán desde entonces."
    return True, ""


def es_administracion(usuario):
    return bool(usuario.is_authenticated and usuario.is_staff)


def acceso_resultados(usuario, votacion):
    """Aplica las reglas de cuándo y a quiénes para un usuario concreto."""
    publicado, motivo = publicados(votacion)
    if es_administracion(usuario):
        return Acceso(permitido=True, vista_previa=not publicado, motivo=motivo)
    if not publicado:
        return Acceso(permitido=False, motivo=motivo)
    if votacion.audiencia_resultados == Votacion.Audiencia.REGISTRADOS and not usuario.is_authenticated:
        return Acceso(permitido=False, requiere_ingreso=True,
                      motivo="Los resultados de esta votación son solo para usuarios registrados.")
    return Acceso(permitido=True)


def contar(votacion):
    """Votos por opción, leídos de MySQL. Incluye las opciones activas y las que ya tienen votos."""
    opciones = (votacion.opciones.annotate(votos_recibidos=Count("votos"))
                .filter(Q(activa=True) | Q(votos_recibidos__gt=0))
                .order_by("-votos_recibidos", "orden", "nombre"))
    filas = [Fila(o.nombre, o.descripcion, o.votos_recibidos, 0.0) for o in opciones]
    total = sum(f.votos for f in filas)
    maximo = max((f.votos for f in filas), default=0)
    for fila in filas:
        fila.porcentaje = round(100 * fila.votos / total, 1) if total else 0.0
        fila.lider = maximo > 0 and fila.votos == maximo
    return Conteo(total=total, filas=filas, lideres=[f for f in filas if f.lider])
