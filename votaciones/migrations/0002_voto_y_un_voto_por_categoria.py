# Entrega 3: crea el modelo Voto con su restricción única y retira «votos por usuario» de Votacion.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("votaciones", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Voto",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "comprobante",
                    models.CharField(
                        editable=False,
                        max_length=16,
                        unique=True,
                        verbose_name="comprobante",
                    ),
                ),
                (
                    "fecha",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="fecha del voto"
                    ),
                ),
            ],
            options={
                "verbose_name": "voto",
                "verbose_name_plural": "votos",
                "ordering": ["-fecha"],
            },
        ),
        migrations.RemoveConstraint(
            model_name="votacion",
            name="votacion_al_menos_un_voto",
        ),
        migrations.RemoveField(
            model_name="votacion",
            name="votos_por_usuario",
        ),
        migrations.AddField(
            model_name="voto",
            name="categoria",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="votos",
                to="votaciones.categoria",
                verbose_name="categoría",
            ),
        ),
        migrations.AddField(
            model_name="voto",
            name="edicion",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="votos",
                to="votaciones.edicion",
                verbose_name="edición",
            ),
        ),
        migrations.AddField(
            model_name="voto",
            name="opcion",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="votos",
                to="votaciones.opcion",
                verbose_name="opción",
            ),
        ),
        migrations.AddField(
            model_name="voto",
            name="usuario",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="votos",
                to=settings.AUTH_USER_MODEL,
                verbose_name="usuario",
            ),
        ),
        migrations.AddField(
            model_name="voto",
            name="votacion",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="votos",
                to="votaciones.votacion",
                verbose_name="votación",
            ),
        ),
        migrations.AddConstraint(
            model_name="voto",
            constraint=models.UniqueConstraint(
                fields=("usuario", "edicion", "categoria"),
                name="voto_unico_usuario_categoria_edicion",
                violation_error_message="Este usuario ya votó en esta categoría de la edición.",
            ),
        ),
    ]
