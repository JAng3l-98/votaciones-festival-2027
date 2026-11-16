"""
Pruebas de la administración en la entrega final: permisos sobre los votos, el grupo
«Administración del Festival», la integridad de lo que ya tiene votos, duplicar una
edición y los votos de prueba.  Ejecutar: python manage.py test votaciones.test_administracion_final -v 2
"""
from datetime import date, datetime, timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .ediciones import duplicar_edicion, un_anio_despues
from .models import Categoria, Edicion, Opcion, Votacion, Voto
from .permisos import GRUPO_ADMINISTRACION
from .servicios import registrar_voto

Usuario = get_user_model()
CLAVE = "Acordeon-Valle-2027"


class BaseAdministracion(TestCase):
    def setUp(self):
        ahora = timezone.now()
        self.edicion = Edicion.objects.create(nombre="Festival de la Leyenda Vallenata 2027", anio=2027, numero=60,
                                              fecha_inicio=date(2027, 4, 28), fecha_fin=date(2027, 5, 1), activa=True)
        self.musica = Categoria.objects.create(edicion=self.edicion, nombre="Música", slug="musica", orden=1)
        self.desfile = Categoria.objects.create(edicion=self.edicion, nombre="Desfile", slug="desfile", orden=2)
        self.cancion = Votacion.objects.create(
            categoria=self.musica, nombre="Canción favorita", slug="cancion", publicacion_resultados="en_vivo",
            fecha_apertura=ahora - timedelta(days=1), fecha_cierre=ahora + timedelta(days=30))
        self.comparsa = Votacion.objects.create(
            categoria=self.desfile, nombre="Comparsa", slug="comparsa",
            fecha_apertura=ahora - timedelta(days=1), fecha_cierre=ahora + timedelta(days=30))
        self.brisa = Opcion.objects.create(votacion=self.cancion, nombre="Brisa del Valle", orden=1)
        Opcion.objects.create(votacion=self.cancion, nombre="Noches del Cesar", orden=2)
        self.alegria = Opcion.objects.create(votacion=self.comparsa, nombre="Comparsa Alegría")
        self.ana = Usuario.objects.create_user(username="ana", email="ana@correo.com", password=CLAVE)
        self.voto = registrar_voto(self.ana, self.cancion, self.brisa.pk)
        self.superusuario = Usuario.objects.create_superuser(username="admin", email="admin@correo.com", password=CLAVE)
        self.equipo = Usuario.objects.create_user(username="equipo", email="equipo@correo.com", password=CLAVE,
                                                  is_staff=True)
        self.equipo.groups.add(Group.objects.get(name=GRUPO_ADMINISTRACION))


class PermisosTests(BaseAdministracion):
    def test_migrate_crea_el_grupo_con_sus_permisos(self):
        grupo = Group.objects.get(name=GRUPO_ADMINISTRACION)
        permisos = set(grupo.permissions.values_list("codename", flat=True))
        self.assertIn("change_votacion", permisos)
        self.assertIn("view_voto", permisos)
        self.assertNotIn("delete_voto", permisos)
        self.assertNotIn("change_voto", permisos)
        self.assertFalse(any(p.endswith("_usuario") for p in permisos))

    def test_ni_el_superusuario_borra_ni_modifica_votos(self):
        self.client.force_login(self.superusuario)
        self.assertEqual(self.client.get(reverse("admin:votaciones_voto_delete", args=[self.voto.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("admin:votaciones_voto_change", args=[self.voto.pk]),
                                          {"opcion": self.brisa.pk}).status_code, 403)
        lista = self.client.get(reverse("admin:votaciones_voto_changelist"))
        self.assertNotContains(lista, "delete_selected")
        self.assertEqual(Voto.objects.count(), 1)

    def test_el_equipo_del_festival_configura_pero_solo_consulta_votos(self):
        self.client.force_login(self.equipo)
        for nombre in ("edicion", "categoria", "votacion", "opcion", "voto"):
            self.assertEqual(self.client.get(reverse(f"admin:votaciones_{nombre}_changelist")).status_code, 200, nombre)
        self.assertEqual(self.client.get(reverse("admin:votaciones_votacion_add")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:votaciones_voto_delete", args=[self.voto.pk])).status_code, 403)
        # Usuarios y grupos son solo del superusuario
        self.assertEqual(self.client.get(reverse("admin:cuentas_usuario_changelist")).status_code, 403)

    def test_un_votante_no_entra_a_la_administracion(self):
        self.client.force_login(self.ana)
        respuesta = self.client.get(reverse("admin:index"))
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse("admin:login"), respuesta["Location"])

    def test_no_se_borra_una_opcion_con_votos(self):
        self.client.force_login(self.superusuario)
        respuesta = self.client.post(reverse("admin:votaciones_opcion_delete", args=[self.brisa.pk]), {"post": "yes"})
        self.assertTrue(Opcion.objects.filter(pk=self.brisa.pk).exists())
        self.assertContains(respuesta, "No se puede eliminar")


class IntegridadTests(BaseAdministracion):
    def test_una_opcion_con_votos_no_pasa_a_otra_votacion(self):
        self.brisa.votacion = self.comparsa
        with self.assertRaisesMessage(ValidationError, "no se puede pasar a otra votación"):
            self.brisa.full_clean()

    def test_una_votacion_con_votos_no_pasa_a_otra_categoria(self):
        self.cancion.categoria = self.desfile
        with self.assertRaisesMessage(ValidationError, "no se puede pasar a otra categoría"):
            self.cancion.full_clean()

    def test_una_categoria_con_votos_no_pasa_a_otra_edicion(self):
        otra = Edicion.objects.create(nombre="Festival 2028", anio=2028)
        self.musica.edicion = otra
        with self.assertRaisesMessage(ValidationError, "no se puede pasar a otra edición"):
            self.musica.full_clean()

    def test_en_el_admin_esos_campos_quedan_de_solo_lectura(self):
        self.client.force_login(self.superusuario)
        formulario = self.client.get(reverse("admin:votaciones_opcion_change", args=[self.brisa.pk]))
        self.assertNotContains(formulario, 'name="votacion"')
        formulario = self.client.get(reverse("admin:votaciones_votacion_change", args=[self.cancion.pk]))
        self.assertNotContains(formulario, 'name="categoria"')
        # Sin votos, la votación sí se puede mover
        formulario = self.client.get(reverse("admin:votaciones_votacion_change", args=[self.comparsa.pk]))
        self.assertContains(formulario, 'name="categoria"')

    def test_la_lista_de_votaciones_muestra_votos_y_enlace_a_resultados(self):
        self.client.force_login(self.equipo)
        respuesta = self.client.get(reverse("admin:votaciones_votacion_changelist"))
        self.assertContains(respuesta, reverse("votaciones:resultados_votacion", args=[self.cancion.pk]))
        fila = next(v for v in respuesta.context["cl"].result_list if v.pk == self.cancion.pk)
        self.assertEqual(fila.votos_recibidos, 1)


class DuplicarEdicionTests(BaseAdministracion):
    def test_un_anio_despues_maneja_el_29_de_febrero(self):
        self.assertEqual(un_anio_despues(date(2028, 2, 29)), date(2029, 2, 28))
        self.assertEqual(un_anio_despues(datetime(2027, 4, 30, 23, 59)), datetime(2028, 4, 30, 23, 59))

    def test_duplica_categorias_votaciones_y_opciones_sin_votos(self):
        nueva, totales = duplicar_edicion(self.edicion)
        self.assertEqual((nueva.anio, nueva.numero, nueva.nombre), (2028, 61, "Festival de la Leyenda Vallenata 2028"))
        self.assertFalse(nueva.activa)
        self.assertEqual(totales, {"categorias": 2, "votaciones": 2, "opciones": 3})
        copia = Votacion.objects.get(categoria__edicion=nueva, slug="cancion")
        self.assertEqual(copia.fecha_cierre, un_anio_despues(self.cancion.fecha_cierre))
        self.assertEqual(copia.publicacion_resultados, "en_vivo")
        self.assertFalse(Voto.objects.filter(edicion=nueva).exists())
        self.edicion.refresh_from_db()
        self.assertTrue(self.edicion.activa)          # el público sigue viendo la edición actual

    def test_no_duplica_si_ya_existe_el_anio_siguiente(self):
        duplicar_edicion(self.edicion)
        with self.assertRaises(ValidationError):
            duplicar_edicion(self.edicion)

    def test_acciones_del_admin_duplicar_y_activar(self):
        self.client.force_login(self.equipo)
        url = reverse("admin:votaciones_edicion_changelist")
        self.client.post(url, {"action": "duplicar_para_el_anio_siguiente", "_selected_action": [self.edicion.pk]})
        nueva = Edicion.objects.get(anio=2028)
        self.client.post(url, {"action": "marcar_como_activa", "_selected_action": [nueva.pk]})
        self.assertEqual(Edicion.objects.activa(), nueva)
        self.edicion.refresh_from_db()
        self.assertFalse(self.edicion.activa)


class VotosDePruebaTests(TestCase):
    def test_carga_votos_que_respetan_las_reglas_y_se_puede_repetir(self):
        call_command("cargar_datos_prueba", verbosity=0)
        call_command("cargar_votos_prueba", votantes=20, stdout=StringIO())
        total = Voto.objects.count()
        self.assertGreater(total, 0)

        call_command("cargar_votos_prueba", votantes=20, stdout=StringIO())
        self.assertEqual(Voto.objects.count(), total)

        votante = Usuario.objects.get(email="votante01@ejemplo.com")
        self.assertFalse(votante.has_usable_password())
        self.assertFalse(Voto.objects.filter(votacion__es_prueba=True).exists())
        self.assertFalse(Voto.objects.filter(votacion__fecha_apertura__gt=timezone.now()).exists())
        for voto in Voto.objects.select_related("votacion"):
            self.assertTrue(voto.votacion.fecha_apertura <= voto.fecha <= voto.votacion.fecha_cierre)
