"""
Pruebas de la consulta administrativa de votos (CP-08).
Ejecutar: python manage.py test votaciones.test_admin_votos -v 2
"""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, Edicion, Opcion, Votacion, Voto
from .servicios import registrar_voto

Usuario = get_user_model()
CLAVE = "Acordeon-Valle-2027"


class AdminVotosTests(TestCase):
    def setUp(self):
        ahora = timezone.now()
        edicion = Edicion.objects.create(nombre="Festival 2027", anio=2027, activa=True)
        self.musica = Categoria.objects.create(edicion=edicion, nombre="Música", slug="musica")
        self.desfile = Categoria.objects.create(edicion=edicion, nombre="Desfile", slug="desfile")
        abre, cierra = ahora - timedelta(days=1), ahora + timedelta(days=30)

        cancion = Votacion.objects.create(
            categoria=self.musica, nombre="Canción favorita", slug="cancion",
            fecha_apertura=abre, fecha_cierre=cierra
        )
        comparsa = Votacion.objects.create(
            categoria=self.desfile, nombre="Comparsa más alegre", slug="comparsa",
            fecha_apertura=abre, fecha_cierre=cierra
        )

        self.brisa = Opcion.objects.create(votacion=cancion, nombre="Brisa del Valle")
        alegria = Opcion.objects.create(votacion=comparsa, nombre="Comparsa Alegría")

        ana = Usuario.objects.create_user(username="ana", email="ana@correo.com", password=CLAVE)
        luis = Usuario.objects.create_user(username="luis", email="luis@correo.com", password=CLAVE)

        self.votos = [
            registrar_voto(ana, cancion, self.brisa.pk),
            registrar_voto(ana, comparsa, alegria.pk),
            registrar_voto(luis, cancion, self.brisa.pk),
        ]

        self.admin = Usuario.objects.create_superuser(
            username="admin", email="admin@correo.com", password=CLAVE
        )
        self.client.force_login(self.admin)

    # CP-08
    def test_cp08_el_administrador_ve_todos_los_votos_guardados(self):
        respuesta = self.client.get(reverse("admin:votaciones_voto_changelist"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.context["cl"].result_count, Voto.objects.count())

        for voto in self.votos:
            self.assertContains(respuesta, voto.comprobante)

    def test_cp08_filtra_los_votos_por_categoria(self):
        respuesta = self.client.get(
            reverse("admin:votaciones_voto_changelist"),
            {"categoria__id__exact": self.musica.pk}
        )
        self.assertEqual(respuesta.context["cl"].result_count, 2)

    def test_cp08_busca_los_votos_por_correo(self):
        respuesta = self.client.get(
            reverse("admin:votaciones_voto_changelist"),
            {"q": "luis@correo.com"}
        )
        self.assertEqual(respuesta.context["cl"].result_count, 1)

    def test_los_votos_no_se_crean_ni_se_modifican_desde_el_admin(self):
        self.assertEqual(
            self.client.get(reverse("admin:votaciones_voto_add")).status_code, 403
        )
        voto = self.votos[0]
        respuesta = self.client.post(
            reverse("admin:votaciones_voto_change", args=[voto.pk]),
            {"opcion": self.brisa.pk}
        )
        self.assertEqual(respuesta.status_code, 403)

    def test_un_miembro_del_equipo_que_no_es_superusuario_no_borra_votos(self):
        apoyo = Usuario.objects.create_user(
            username="apoyo", email="apoyo@correo.com",
            password=CLAVE, is_staff=True
        )
        apoyo.user_permissions.add(
            *Permission.objects.filter(codename__in=["view_voto", "delete_voto"])
        )
        self.client.force_login(apoyo)

        self.assertEqual(
            self.client.get(reverse("admin:votaciones_voto_changelist")).status_code, 200
        )
        self.assertEqual(
            self.client.get(
                reverse("admin:votaciones_voto_delete", args=[self.votos[0].pk])
            ).status_code, 403
        )

    def test_la_regla_de_votos_se_ve_en_categorias_y_no_se_cambia_si_hay_votos(self):
        lista = self.client.get(reverse("admin:votaciones_categoria_changelist"))
        self.assertContains(lista, "Un solo voto en toda la categoría")

        url = reverse(
            "admin:votaciones_categoria_change", args=[self.musica.pk]
        )
        datos = {
            "edicion": self.musica.edicion_id,
            "nombre": "Música",
            "slug": "musica",
            "descripcion": "",
            "orden": 0,
            "visible": "on",
            "regla_voto": "votacion",
        }
        respuesta = self.client.post(url, datos)
        self.assertContains(respuesta, "ya tiene votos")

        self.musica.refresh_from_db()
        self.assertEqual(self.musica.regla_voto, "categoria")

    def test_la_lista_de_opciones_muestra_cuantos_votos_tiene_cada_una(self):
        respuesta = self.client.get(
            reverse("admin:votaciones_opcion_changelist")
        )
        fila = next(
            o for o in respuesta.context["cl"].result_list
            if o.pk == self.brisa.pk
        )
        self.assertEqual(fila.votos_recibidos, 2)
