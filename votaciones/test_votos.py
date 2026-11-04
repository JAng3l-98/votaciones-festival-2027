"""
Pruebas automáticas del módulo de votaciones (Entrega 3).

Cada prueba lleva en el nombre el caso de la guía que respalda (CP-01 a CP-10).
CP-07 (mis votos) y CP-08 (consulta en el Admin) tienen sus propias pruebas en
cuentas/test_mis_votos.py y votaciones/test_admin_votos.py.

Ejecutar:  python manage.py test votaciones.test_votos -v 2
"""
import json
import threading
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection, transaction
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, Edicion, Opcion, Votacion, Voto
from .servicios import VotoDuplicado, VotoRechazado, registrar_voto

Usuario = get_user_model()
CLAVE = "Clave-de-prueba-2027"   # solo existe en la base de datos temporal de las pruebas


def crear_datos(prueba):
    """Edición activa con dos categorías: Música (dos votaciones abiertas) y Desfile (una abierta)."""
    ahora = timezone.now()
    prueba.edicion = Edicion.objects.create(nombre="Festival 2027", anio=2027, numero=60, activa=True)
    prueba.musica = Categoria.objects.create(edicion=prueba.edicion, nombre="Música", slug="musica")
    prueba.desfile = Categoria.objects.create(edicion=prueba.edicion, nombre="Desfile", slug="desfile")

    def votacion(categoria, nombre, abre, cierra, opciones):
        v = Votacion.objects.create(categoria=categoria, nombre=nombre, slug=nombre.lower().replace(" ", "-"),
                                    fecha_apertura=ahora + abre, fecha_cierre=ahora + cierra)
        for i, nombre_opcion in enumerate(opciones, start=1):
            Opcion.objects.create(votacion=v, nombre=nombre_opcion, orden=i)
        return v

    dia = timedelta(days=1)
    prueba.cancion = votacion(prueba.musica, "Cancion favorita", -dia, 30 * dia, ["Cancion A", "Cancion B"])
    prueba.agrupacion = votacion(prueba.musica, "Agrupacion favorita", -dia, 30 * dia, ["Agrupacion A", "Agrupacion B"])
    prueba.comparsa = votacion(prueba.desfile, "Comparsa mas alegre", -dia, 30 * dia, ["Comparsa A", "Comparsa B"])
    prueba.usuario = Usuario.objects.create_user(username="ana", email="ana@ejemplo.com", password=CLAVE, first_name="Ana")


def opcion(votacion, indice=0):
    return votacion.opciones.order_by("orden")[indice]


class VotoTests(TestCase):
    def setUp(self):
        crear_datos(self)
        self.client.force_login(self.usuario)

    def votar(self, votacion, opcion_elegida):
        return self.client.post(reverse("votaciones:votar", args=[votacion.pk]), {"opcion": opcion_elegida.pk})

    # ------------------------------------------------------------ CP-01
    def test_cp01_voto_valido_se_registra_en_la_base_de_datos(self):
        elegida = opcion(self.cancion, 1)
        confirmacion = self.client.post(reverse("votaciones:confirmar", args=[self.cancion.pk]), {"opcion": elegida.pk})
        self.assertContains(confirmacion, elegida.nombre)
        self.assertEqual(Voto.objects.count(), 0, "Confirmar todavía no debe guardar el voto")

        respuesta = self.votar(self.cancion, elegida)
        voto = Voto.objects.get()
        self.assertRedirects(respuesta, reverse("votaciones:voto_registrado", args=[voto.comprobante]))
        self.assertEqual((voto.usuario, voto.edicion, voto.categoria, voto.votacion, voto.opcion),
                         (self.usuario, self.edicion, self.musica, self.cancion, elegida))
        self.assertContains(self.client.get(respuesta.url), voto.comprobante)

    # ------------------------------------------------------------ CP-02
    def test_cp02_segundo_voto_en_la_misma_votacion_se_rechaza(self):
        self.votar(self.cancion, opcion(self.cancion, 0))
        respuesta = self.votar(self.cancion, opcion(self.cancion, 1))
        self.assertRedirects(respuesta, self.cancion.get_absolute_url(), fetch_redirect_response=False)
        self.assertContains(self.client.get(respuesta.url), "Ya votaste en la categoría")
        self.assertEqual(Voto.objects.count(), 1)
        self.assertEqual(Voto.objects.get().opcion, opcion(self.cancion, 0))

    def test_cp02_segundo_voto_en_otro_subevento_de_la_misma_categoria_se_rechaza(self):
        self.votar(self.cancion, opcion(self.cancion))
        self.votar(self.agrupacion, opcion(self.agrupacion))   # misma categoría Música, otra votación
        self.assertEqual(Voto.objects.filter(categoria=self.musica).count(), 1)

    # ------------------------------------------------------------ CP-03
    def test_cp03_voto_en_otra_categoria_se_permite(self):
        self.votar(self.cancion, opcion(self.cancion))
        self.votar(self.comparsa, opcion(self.comparsa))
        self.assertEqual(Voto.objects.filter(usuario=self.usuario).count(), 2)
        self.assertEqual(set(Voto.objects.values_list("categoria__nombre", flat=True)), {"Música", "Desfile"})

    # ------------------------------------------------------------ CP-04
    def test_cp04_usuario_no_autenticado_debe_iniciar_sesion(self):
        anonimo = Client()
        for nombre in ("confirmar", "votar"):
            respuesta = anonimo.post(reverse(f"votaciones:{nombre}", args=[self.cancion.pk]), {"opcion": opcion(self.cancion).pk})
            self.assertEqual(respuesta.status_code, 302)
            self.assertIn(reverse("cuentas:login"), respuesta.url)
            self.assertIn("next=", respuesta.url)
        self.assertEqual(Voto.objects.count(), 0)

    # ------------------------------------------------------------ CP-05
    def test_cp05_votacion_cerrada_se_rechaza(self):
        self.cancion.fecha_apertura = timezone.now() - timedelta(days=10)
        self.cancion.fecha_cierre = timezone.now() - timedelta(days=1)
        self.cancion.save()
        self.votar(self.cancion, opcion(self.cancion))
        self.assertEqual(Voto.objects.count(), 0)

    def test_cp05_votacion_que_aun_no_abre_se_rechaza(self):
        self.cancion.fecha_apertura = timezone.now() + timedelta(days=1)
        self.cancion.save()
        with self.assertRaisesMessage(VotoRechazado, "todavía no está abierta"):
            registrar_voto(self.usuario, self.cancion, opcion(self.cancion).pk)
        self.assertEqual(Voto.objects.count(), 0)

    def test_cp05_categoria_oculta_o_de_otra_edicion_se_rechaza(self):
        self.musica.visible = False
        self.musica.save()
        with self.assertRaisesMessage(VotoRechazado, "no está habilitada"):
            registrar_voto(self.usuario, self.cancion, opcion(self.cancion).pk)
        Edicion.objects.create(nombre="Festival 2028", anio=2028, activa=True)   # la 2027 deja de estar activa
        with self.assertRaisesMessage(VotoRechazado, "no está habilitada"):
            registrar_voto(self.usuario, self.comparsa, opcion(self.comparsa).pk)
        self.assertEqual(Voto.objects.count(), 0)

    # ------------------------------------------------------------ CP-06
    def test_cp06_opcion_de_otra_categoria_se_rechaza(self):
        ajena = opcion(self.comparsa)                           # opción de Desfile enviada a Música
        respuesta = self.votar(self.cancion, ajena)
        self.assertContains(self.client.get(respuesta.url), "no pertenece a esta votación")
        self.assertEqual(Voto.objects.count(), 0)

    def test_cp06_opcion_inexistente_o_inactiva_se_rechaza(self):
        inactiva = opcion(self.cancion)
        inactiva.activa = False
        inactiva.save()
        for valor in (inactiva.pk, 999999, "abc", ""):
            with self.assertRaises(VotoRechazado):
                registrar_voto(self.usuario, self.cancion, valor)
        self.assertEqual(Voto.objects.count(), 0)

    # ------------------------------------------------------------ CP-09 (integridad)
    def test_cp09_la_base_de_datos_impide_un_voto_duplicado(self):
        Voto.objects.create(usuario=self.usuario, opcion=opcion(self.cancion))
        with self.assertRaises(IntegrityError), transaction.atomic():
            Voto.objects.create(usuario=self.usuario, opcion=opcion(self.agrupacion))   # misma categoría
        self.assertEqual(Voto.objects.count(), 1)

    def test_cp09_si_dos_solicitudes_pasan_la_validacion_solo_se_guarda_una(self):
        # Simula la carrera: la segunda solicitud no alcanza a ver el primer voto en la validación,
        # pero la restricción única de la base de datos la detiene al guardar.
        registrar_voto(self.usuario, self.cancion, opcion(self.cancion).pk)
        with mock.patch("votaciones.servicios.voto_que_bloquea", side_effect=[None, Voto.objects.get()]):
            with self.assertRaises(VotoDuplicado):
                registrar_voto(self.usuario, self.agrupacion, opcion(self.agrupacion).pk)
        self.assertEqual(Voto.objects.count(), 1)

    # ------------------------------------------------------------ Regla configurable por categoría
    def test_regla_un_voto_por_votacion_permite_votar_en_cada_subevento_una_vez(self):
        self.musica.regla_voto = Categoria.ReglaVoto.UNO_POR_VOTACION
        self.musica.save()
        self.votar(self.cancion, opcion(self.cancion, 0))
        self.votar(self.agrupacion, opcion(self.agrupacion, 0))         # otra votación de Música: se permite
        respuesta = self.votar(self.cancion, opcion(self.cancion, 1))    # misma votación otra vez: se rechaza
        self.assertContains(self.client.get(respuesta.url), "se permite un voto en cada votación")
        self.assertEqual(Voto.objects.filter(categoria=self.musica).count(), 2)
        self.assertEqual(Voto.objects.filter(votacion=self.cancion).count(), 1)

    def test_regla_un_voto_por_votacion_tambien_la_protege_la_base_de_datos(self):
        self.musica.regla_voto = Categoria.ReglaVoto.UNO_POR_VOTACION
        self.musica.save()
        Voto.objects.create(usuario=self.usuario, opcion=opcion(self.cancion, 0))
        Voto.objects.create(usuario=self.usuario, opcion=opcion(self.agrupacion, 0))
        with self.assertRaises(IntegrityError), transaction.atomic():
            Voto.objects.create(usuario=self.usuario, opcion=opcion(self.cancion, 1))
        self.assertEqual(Voto.objects.count(), 2)

    def test_la_regla_no_se_puede_cambiar_si_la_categoria_ya_tiene_votos(self):
        registrar_voto(self.usuario, self.cancion, opcion(self.cancion).pk)
        self.musica.regla_voto = Categoria.ReglaVoto.UNO_POR_VOTACION
        with self.assertRaises(ValidationError):
            self.musica.full_clean()
        self.desfile.regla_voto = Categoria.ReglaVoto.UNO_POR_VOTACION   # sin votos: sí se puede
        self.desfile.full_clean()

    # ------------------------------------------------------------ Seguridad
    def test_votar_exige_post_y_token_csrf(self):
        self.assertEqual(self.client.get(reverse("votaciones:votar", args=[self.cancion.pk])).status_code, 405)
        sin_csrf = Client(enforce_csrf_checks=True)
        sin_csrf.force_login(self.usuario)
        respuesta = sin_csrf.post(reverse("votaciones:votar", args=[self.cancion.pk]), {"opcion": opcion(self.cancion).pk})
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(Voto.objects.count(), 0)

    def test_comprobante_solo_lo_ve_su_dueno(self):
        voto = registrar_voto(self.usuario, self.cancion, opcion(self.cancion).pk)
        otro = Usuario.objects.create_user(username="luis", email="luis@ejemplo.com", password=CLAVE)
        self.client.force_login(otro)
        self.assertEqual(self.client.get(reverse("votaciones:voto_registrado", args=[voto.comprobante])).status_code, 404)

    def test_detalle_muestra_el_voto_en_lugar_del_formulario(self):
        registrar_voto(self.usuario, self.cancion, opcion(self.cancion).pk)
        respuesta = self.client.get(self.agrupacion.get_absolute_url())   # otra votación de la misma categoría
        self.assertFalse(respuesta.context["puede_votar"])
        self.assertEqual(respuesta.context["voto_usuario"].opcion, opcion(self.cancion))


class ApiCategoriasTests(TestCase):
    def setUp(self):
        crear_datos(self)

    # ------------------------------------------------------------ CP-10
    def test_cp10_api_devuelve_json_con_categorias_y_opciones(self):
        respuesta = self.client.get("/api/categorias/")
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta["Content-Type"], "application/json")
        datos = json.loads(respuesta.content)   # falla si no es JSON válido
        self.assertEqual(datos["edicion"]["anio"], 2027)
        self.assertEqual([c["nombre"] for c in datos["categorias"]], ["Desfile", "Música"])
        musica = datos["categorias"][1]
        votaciones = {v["nombre"]: v for v in musica["votaciones"]}
        self.assertEqual(set(votaciones), {"Cancion favorita", "Agrupacion favorita"})
        self.assertEqual([o["nombre"] for o in votaciones["Cancion favorita"]["opciones"]], ["Cancion A", "Cancion B"])
        self.assertEqual(musica["total_opciones"], 4)
        self.assertEqual(musica["regla_voto"], "categoria")   # regla por defecto: un voto en toda la categoría

    def test_api_omite_lo_oculto_y_no_expone_votos_ni_usuarios(self):
        self.desfile.visible = False
        self.desfile.save()
        Voto.objects.create(usuario=self.usuario, opcion=opcion(self.cancion))
        texto = self.client.get("/api/categorias/").content.decode()
        self.assertNotIn("Desfile", texto)
        self.assertNotIn("ana@ejemplo.com", texto)

    def test_api_solo_acepta_get(self):
        self.assertEqual(self.client.post("/api/categorias/").status_code, 405)

    def test_api_permite_consultar_otra_edicion_por_anio(self):
        self.assertEqual(self.client.get("/api/categorias/?edicion=1990").status_code, 404)
        self.assertEqual(json.loads(self.client.get("/api/categorias/?edicion=2027").content)["edicion"]["numero"], 60)


class ConcurrenciaTests(TransactionTestCase):
    """CP-09: dos solicitudes simultáneas a la misma categoría; cada una con su propia conexión a la base de datos."""

    def setUp(self):
        crear_datos(self)

    def test_cp09_solicitudes_simultaneas_dejan_un_solo_voto(self):
        if connection.vendor == "sqlite" and connection.settings_dict["NAME"].startswith(("file:memorydb", ":memory:")):
            self.skipTest("La prueba de concurrencia necesita MySQL (o SQLite en archivo).")
        barrera = threading.Barrier(2)
        resultados = []

        def solicitud(votacion):
            cliente = Client()
            cliente.force_login(self.usuario)
            barrera.wait()                                   # las dos salen al mismo tiempo
            try:
                r = cliente.post(reverse("votaciones:votar", args=[votacion.pk]), {"opcion": opcion(votacion).pk})
                resultados.append("registrado" if "/votos/" in r.url else "rechazado")
            finally:
                connection.close()

        hilos = [threading.Thread(target=solicitud, args=(v,)) for v in (self.cancion, self.agrupacion)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()
        self.assertEqual(sorted(resultados), ["rechazado", "registrado"])
        self.assertEqual(Voto.objects.filter(usuario=self.usuario, categoria=self.musica).count(), 1)
