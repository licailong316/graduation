# Generated by Django 4.2.3 on 2024-04-21 08:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gp', '0003_alter_basin_basin_id_alter_data_id_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='data',
            unique_together={('province', 'city', 'basin', 'river', 'section', 'monitoring_time')},
        ),
    ]
