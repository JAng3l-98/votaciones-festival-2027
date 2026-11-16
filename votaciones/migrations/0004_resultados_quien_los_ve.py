# Entrega final: a quiénes se muestran los resultados (y ayuda de cuándo se publican).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("votaciones", "0003_regla_de_votos_configurable"),
    ]

    operations = [
        migrations.AddField(
            model_name="votacion",
            name="audiencia_resultados",
            field=models.CharField(
                choices=[
                    ("publico", "Todo el público"),
                    ("registrados", "Solo usuarios registrados"),
                ],
                default="publico",
                help_text="A quiénes se muestran los resultados publicados. La administración los ve siempre.",
                max_length=12,
                verbose_name="quién ve los resultados",
            ),
        ),
        migrations.AlterField(
            model_name="votacion",
            name="publicacion_resultados",
            field=models.CharField(
                choices=[
                    ("al_cierre", "Al cierre de la votación"),
                    ("en_vivo", "En vivo"),
                    ("no_publicar", "No publicar"),
                ],
                default="al_cierre",
                help_text="Cuándo ve el público los resultados: en vivo, al cierre de la votación o nunca.",
                max_length=20,
                verbose_name="publicación de resultados",
            ),
        ),
    ]
