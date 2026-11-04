# Entrega 3: regla de votos configurable por categoría (un voto en toda la categoría o uno por votación).

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("votaciones", "0002_voto_y_un_voto_por_categoria"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="voto",
            name="voto_unico_usuario_categoria_edicion",
        ),
        migrations.AddField(
            model_name="categoria",
            name="regla_voto",
            field=models.CharField(
                choices=[
                    ("categoria", "Un solo voto en toda la categoría"),
                    ("votacion", "Un voto en cada votación de la categoría"),
                ],
                default="categoria",
                help_text="Un solo voto en toda la categoría (regla de la Entrega 3) o un voto en cada una de sus votaciones. No se puede cambiar cuando la categoría ya tiene votos.",
                max_length=12,
                verbose_name="regla de votos",
            ),
        ),
        migrations.AddField(
            model_name="voto",
            name="alcance",
            field=models.PositiveBigIntegerField(
                default=0, editable=False, verbose_name="alcance de la regla"
            ),
        ),
        migrations.AddConstraint(
            model_name="voto",
            constraint=models.UniqueConstraint(
                fields=("usuario", "edicion", "categoria", "alcance"),
                name="voto_unico_usuario_categoria_edicion",
                violation_error_message="Este usuario ya votó en esta categoría de la edición.",
            ),
        ),
    ]
