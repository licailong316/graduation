# Generated by Django 4.2.3 on 2024-03-10 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gp', '0002_alter_city_city_id_alter_province_province_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='basin',
            name='basin_id',
            field=models.AutoField(primary_key=True, serialize=False, verbose_name='流域ID'),
        ),
        migrations.AlterField(
            model_name='data',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='river',
            name='river_id',
            field=models.AutoField(primary_key=True, serialize=False, verbose_name='河流ID'),
        ),
        migrations.AlterField(
            model_name='section',
            name='section_id',
            field=models.AutoField(primary_key=True, serialize=False, verbose_name='断面ID'),
        ),
        migrations.AlterField(
            model_name='user',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False, verbose_name='用户ID'),
        ),
    ]
