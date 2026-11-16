"""
Pruebas de los resultados (entrega final): cuándo se publican, a quiénes se muestran y
cómo se cuentan.  Ejecutar: python manage.py test votaciones.test_resultados -v 2
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, Edicion, Opcion, Votacion, Voto
from .resultados import acceso_resultados, contar

Usuario = get_user_model()
CLAVE = "Acordeon-Valle-2027"


class ResultadosTests(TestCase):
    def setUp(self):
        ahora = timezone.now()
        self.abierta = dict(fecha_apertura=ahora - timedelta(days=2), fecha_cierre=ahora + timedelta(days=5))
        self.cerrada = dict(fecha_apertura=ahora - timedelta(days=9), fecha_cierre=ahora - timedelta(days=1))
        self.proxima = dict(fecha_apertura=ahora + timedelta(days=3), fecha_cierre=ahora + timedelta(days=6))
        edicion = Edicion.objects.create(nombre="Festival 2027", anio=2027, activa=True)
        # Un voto en cada votación, para poder cargar votos en todas desde los mismos usuarios.
        self.categoria = Categoria.objects.create(edicion=edicion, nombre="Música", slug="musica",
                                                  regla_voto=Categoria.ReglaVoto.UNO_POR_VOTACION)
        self.votantes = [Usuario.objects.create_user(username=f"v{i}", email=f"v{i}@correo.com", password=CLAVE)
                         for i in range(5)]
        self.admin = Usuario.objects.create_user(username="equipo", email="equipo@correo.com",
                                                 password=CLAVE, is_staff=True)

    def votacion(self, nombre, fechas, votos=(3, 1), **campos):
        """Crea una votación con dos opciones y los votos indicados para cada una."""
        votacion = Votacion.objects.create(categoria=self.categoria, nombre=nombre, slug=nombre.lower().replace(" ", "-"),
                                           **fechas, **campos)
        opciones = [Opcion.objects.create(votacion=votacion, nombre=f"{nombre} A", orden=1),
                    Opcion.objects.create(votacion=votacion, nombre=f"{nombre} B", orden=2)]
        votantes = iter(self.votantes)
        for opcion, cantidad in zip(opciones, votos):
            for _ in range(cantidad):
                Voto.objects.create(usuario=next(votantes), opcion=opcion)
        return votacion

    def ver(self, votacion):
        return self.client.get(reverse("votaciones:resultados_votacion", args=[votacion.pk]))

    # ---------------------------------------------------------------- Conteo
    def test_cuenta_votos_porcentajes_y_quien_va_ganando(self):
        votacion = self.votacion("Comparsa", self.abierta, publicacion_resultados="en_vivo")
        conteo = contar(votacion)
        self.assertEqual(conteo.total, 4)
        self.assertEqual([(f.nombre, f.votos, f.porcentaje) for f in conteo.filas],
                         [("Comparsa A", 3, 75.0), ("Comparsa B", 1, 25.0)])
        self.assertEqual([f.nombre for f in conteo.lideres], ["Comparsa A"])
        self.assertFalse(conteo.empate)

    def test_detecta_empate(self):
        votacion = self.votacion("Comparsa", self.abierta, votos=(2, 2), publicacion_resultados="en_vivo")
        self.assertTrue(contar(votacion).empate)
        self.assertContains(self.ver(votacion), "Van empatados")

    def test_una_opcion_retirada_conserva_sus_votos_y_una_sin_votos_no_aparece(self):
        votacion = self.votacion("Comparsa", self.abierta, votos=(3, 0), publicacion_resultados="en_vivo")
        votacion.opciones.update(activa=False)
        nombres = [f.nombre for f in contar(votacion).filas]
        self.assertEqual(nombres, ["Comparsa A"])

    # ---------------------------------------------------------------- Cuándo se publican
    def test_en_vivo_el_publico_ve_resultados_parciales(self):
        votacion = self.votacion("Comparsa", self.abierta, publicacion_resultados="en_vivo")
        respuesta = self.ver(votacion)
        self.assertContains(respuesta, "Resultados parciales")
        self.assertContains(respuesta, "Va ganando Comparsa A")
        self.assertContains(respuesta, "75,0 %")
        self.assertNotContains(respuesta, "Vista previa")

    def test_al_cierre_el_publico_no_ve_nada_mientras_esta_abierta(self):
        votacion = self.votacion("Canción", self.abierta, publicacion_resultados="al_cierre")
        respuesta = self.ver(votacion)
        self.assertContains(respuesta, "Resultados aún no disponibles")
        self.assertContains(respuesta, "al cierre de la votación")
        self.assertNotContains(respuesta, "Canción A")
        self.assertNotIn("conteo", respuesta.context)

    def test_al_cierre_se_publica_el_resultado_final(self):
        votacion = self.votacion("Presentación", self.cerrada, publicacion_resultados="al_cierre")
        respuesta = self.ver(votacion)
        self.assertContains(respuesta, "Resultado final")
        self.assertContains(respuesta, "Ganó Presentación A")

    def test_no_publicar_nunca_se_muestra_al_publico(self):
        votacion = self.votacion("Interna", self.cerrada, publicacion_resultados="no_publicar")
        self.assertContains(self.ver(votacion), "no se publican")
        self.assertNotIn("conteo", self.ver(votacion).context)

    def test_una_votacion_proxima_no_muestra_resultados_aunque_sea_en_vivo(self):
        votacion = self.votacion("Piloneras", self.proxima, votos=(0, 0), publicacion_resultados="en_vivo")
        self.assertFalse(acceso_resultados(self.votantes[0], votacion).permitido)

    def test_una_votacion_de_prueba_no_publica_resultados(self):
        votacion = self.votacion("Ensayo", self.abierta, publicacion_resultados="en_vivo", es_prueba=True)
        respuesta = self.ver(votacion)
        self.assertContains(respuesta, "votación de prueba")
        self.assertNotIn("conteo", respuesta.context)

    # ---------------------------------------------------------------- A quiénes se muestran
    def test_solo_registrados_pide_ingresar_y_luego_los_muestra(self):
        votacion = self.votacion("Comparsa", self.abierta, publicacion_resultados="en_vivo",
                                 audiencia_resultados="registrados")
        respuesta = self.ver(votacion)
        self.assertContains(respuesta, "solo para usuarios registrados")
        self.assertContains(respuesta, "Ingresar para ver los resultados")
        self.assertNotIn("conteo", respuesta.context)

        self.client.force_login(self.votantes[0])
        self.assertContains(self.ver(votacion), "Va ganando Comparsa A")

    def test_la_administracion_ve_una_vista_previa_antes_de_publicar(self):
        votacion = self.votacion("Canción", self.abierta, publicacion_resultados="al_cierre")
        self.client.force_login(self.admin)
        respuesta = self.ver(votacion)
        self.assertContains(respuesta, "Vista previa de la administración")
        self.assertContains(respuesta, "Va ganando Canción A")
        self.assertContains(respuesta, "Descargar CSV")

    def test_un_votante_no_ve_la_vista_previa(self):
        votacion = self.votacion("Canción", self.abierta, publicacion_resultados="al_cierre")
        self.client.force_login(self.votantes[0])
        self.assertNotIn("conteo", self.ver(votacion).context)

    def test_una_votacion_oculta_solo_la_ve_la_administracion(self):
        votacion = self.votacion("Oculta", self.abierta, publicacion_resultados="en_vivo", visible=False)
        self.assertEqual(self.ver(votacion).status_code, 404)
        self.client.force_login(self.admin)
        self.assertEqual(self.ver(votacion).status_code, 200)

    # ---------------------------------------------------------------- Lista, detalle y CSV
    def test_la_lista_solo_muestra_conteos_publicados(self):
        self.votacion("Comparsa", self.abierta, votos=(3, 2), publicacion_resultados="en_vivo")
        self.votacion("Canción", self.abierta, votos=(1, 1), publicacion_resultados="al_cierre")
        respuesta = self.client.get(reverse("votaciones:resultados"))
        self.assertContains(respuesta, "5 votos")
        self.assertNotContains(respuesta, "2 votos")
        self.assertContains(respuesta, "Ver resultados", count=1)

    def test_el_detalle_explica_la_regla_y_enlaza_los_resultados(self):
        votacion = self.votacion("Comparsa", self.abierta, publicacion_resultados="en_vivo")
        respuesta = self.client.get(votacion.get_absolute_url())
        self.assertContains(respuesta, "se publican en vivo, mientras la votación está abierta, para todo el público")
        self.assertContains(respuesta, votacion.get_resultados_url())

    def test_el_csv_es_solo_para_la_administracion(self):
        votacion = self.votacion("Comparsa", self.abierta, publicacion_resultados="en_vivo")
        url = reverse("votaciones:resultados_csv", args=[votacion.pk])
        self.assertEqual(self.client.get(url).status_code, 302)          # al ingreso de la administración
        self.client.force_login(self.votantes[0])
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.admin)
        respuesta = self.client.get(url)
        self.assertEqual(respuesta["Content-Type"], "text/csv; charset=utf-8")
        contenido = respuesta.content.decode("utf-8-sig")
        self.assertIn("Comparsa;Comparsa A;3;75,0", contenido)
        self.assertIn("Comparsa;Total;4;100,0", contenido)
