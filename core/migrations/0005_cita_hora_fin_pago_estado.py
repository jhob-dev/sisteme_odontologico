import datetime

from django.db import migrations, models


def convertir_estados_pagos(apps, schema_editor):
    Pago = apps.get_model('core', 'Pago')
    Pago.objects.filter(estado='completado').update(estado='pagado')
    Pago.objects.filter(estado='anulado').update(estado='no_pagado')


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_remove_historiaclinica_alergias_and_more'),
    ]

    operations = [
        migrations.RunPython(convertir_estados_pagos, migrations.RunPython.noop),
        migrations.AddField(
            model_name='cita',
            name='hora_fin',
            field=models.TimeField(default=datetime.time(9, 0)),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='pago',
            name='estado',
            field=models.CharField(
                choices=[
                    ('pendiente', 'Pendiente'),
                    ('pagado', 'Pagado'),
                    ('no_pagado', 'No Pagado'),
                ],
                default='pagado',
                max_length=20,
            ),
        ),
    ]
