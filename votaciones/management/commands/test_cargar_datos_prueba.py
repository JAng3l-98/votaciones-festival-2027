from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from votaciones.models import Edicion, Categoria, Votacion, Opcion


class CargarDatosPruebaTests(TestCase):

    def ejecutar_comando(self):
        salida = StringIO()
        call_command("cargar_datos_prueba", stdout=salida)
        return salida.getvalue()

    def test_crea_una_edicion(self):
        self.ejecutar_comando()
        self.assertEqual(Edicion.objects.count(), 1)

    def test_crea_cuatro_categorias(self):
        self.ejecutar_comando()
        self.assertEqual(Categoria.objects.count(), 4)

    def test_crea_seis_votaciones(self):
        self.ejecutar_comando()
        self.assertEqual(Votacion.objects.count(), 6)

    def test_crea_dieciocho_opciones(self):
        self.ejecutar_comando()
        self.assertEqual(Opcion.objects.count(), 18)

    def test_segunda_ejecucion_no_duplica_registros(self):
        self.ejecutar_comando()
        cantidades_primera = (
            Edicion.objects.count(),
            Categoria.objects.count(),
            Votacion.objects.count(),
            Opcion.objects.count(),
        )

        salida_segunda = self.ejecutar_comando()

        cantidades_segunda = (
            Edicion.objects.count(),
            Categoria.objects.count(),
            Votacion.objects.count(),
            Opcion.objects.count(),
        )

        self.assertEqual(cantidades_primera, cantidades_segunda)
        self.assertIn("La edicion ya existia.", salida_segunda)
