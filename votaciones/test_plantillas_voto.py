from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Categoria, Edicion, Opcion, Votacion
from .servicios import registrar_voto

Usuario = get_user_model()


class PantallasVotoTests(TestCase):
    def setUp(self):
        ahora = timezone.now()
        edicion = Edicion.objects.create(nombre="Festival 2027", anio=2027, activa=True)
        musica = Categoria.objects.create(edicion=edicion, nombre="Música", slug="musica")
        self.cancion = Votacion.objects.create(categoria=musica, nombre="Canción favorita", slug="cancion",
                                               fecha_apertura=ahora - timedelta(days=1), fecha_cierre=ahora + timedelta(days=30))
        self.brisa = Opcion.objects.create(votacion=self.cancion, nombre="Brisa del Valle", orden=1)
        self.noches = Opcion.objects.create(votacion=self.cancion, nombre="Noches del Cesar", orden=2)
        self.ana = Usuario.objects.create_user(username="ana", email="ana@correo.com", password="Acordeon-Valle-2027",
                                               first_name="Ana", last_name="Pérez")

    def test_sin_sesion_se_ven_las_opciones_y_el_boton_para_ingresar(self):
        respuesta = self.client.get(self.cancion.get_absolute_url())
        self.assertContains(respuesta, "Brisa del Valle")
        self.assertContains(respuesta, f"{reverse('cuentas:login')}?next=")
        self.assertNotContains(respuesta, 'type="radio"')

    def test_con_sesion_se_elige_una_opcion_en_un_formulario_post_con_csrf(self):
        self.client.force_login(self.ana)
        respuesta = self.client.get(self.cancion.get_absolute_url())
        self.assertContains(respuesta, 'type="radio" name="opcion"', count=2)
        self.assertContains(respuesta, 'method="post"')
        self.assertContains(respuesta, "csrfmiddlewaretoken")
        self.assertContains(respuesta, reverse("votaciones:confirmar", args=[self.cancion.pk]))

    def test_la_confirmacion_muestra_el_resumen_del_voto(self):
        self.client.force_login(self.ana)
        respuesta = self.client.post(reverse("votaciones:confirmar", args=[self.cancion.pk]), {"opcion": self.noches.pk})
        self.assertContains(respuesta, "Revisa tu voto")
        self.assertContains(respuesta, "Noches del Cesar")
        self.assertContains(respuesta, "ana@correo.com")
        self.assertContains(respuesta, f'name="opcion" value="{self.noches.pk}"')
        self.assertContains(respuesta, "Confirmar voto")

    def test_el_comprobante_muestra_codigo_y_datos_del_voto(self):
        voto = registrar_voto(self.ana, self.cancion, self.brisa.pk)
        self.client.force_login(self.ana)
        respuesta = self.client.get(reverse("votaciones:voto_registrado", args=[voto.comprobante]))
        self.assertContains(respuesta, "Tu voto quedó registrado")
        self.assertContains(respuesta, voto.comprobante)
        self.assertContains(respuesta, "Brisa del Valle")

    def test_si_ya_voto_se_muestra_el_aviso_y_no_el_formulario(self):
        registrar_voto(self.ana, self.cancion, self.brisa.pk)
        self.client.force_login(self.ana)
        respuesta = self.client.get(self.cancion.get_absolute_url())
        self.assertContains(respuesta, "Ya votaste en la categoría")
        self.assertNotContains(respuesta, 'type="radio"')

    def test_con_un_voto_por_votacion_el_aviso_lo_explica(self):
        self.cancion.categoria.regla_voto = "votacion"
        self.cancion.categoria.save()
        registrar_voto(self.ana, self.cancion, self.brisa.pk)
        self.client.force_login(self.ana)
        respuesta = self.client.get(self.cancion.get_absolute_url())
        self.assertContains(respuesta, "Ya votaste en esta votación")
        self.assertContains(respuesta, "puedes votar una vez en cada una de sus votaciones")

    def test_votacion_cerrada_no_muestra_el_formulario(self):
        self.cancion.fecha_apertura = timezone.now() - timedelta(days=5)
        self.cancion.fecha_cierre = timezone.now() - timedelta(days=1)
        self.cancion.save()
        self.client.force_login(self.ana)
        respuesta = self.client.get(self.cancion.get_absolute_url())
        self.assertContains(respuesta, "ya cerró")
        self.assertNotContains(respuesta, 'type="radio"')

