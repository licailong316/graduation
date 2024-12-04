# Generated by Django 4.2.3 on 2024-05-18 05:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gp', '0006_delete_dataview'),
    ]

    operations = [
        migrations.DeleteModel(
            name='User',
        ),
        migrations.AlterModelOptions(
            name='basin',
            options={'verbose_name': '流域', 'verbose_name_plural': '流域信息'},
        ),
        migrations.AlterModelOptions(
            name='city',
            options={'verbose_name': '城市', 'verbose_name_plural': '城市信息'},
        ),
        migrations.AlterModelOptions(
            name='data',
            options={'verbose_name': '数据', 'verbose_name_plural': '水质信息'},
        ),
        migrations.AlterModelOptions(
            name='province',
            options={'verbose_name': '省份', 'verbose_name_plural': '省份信息'},
        ),
        migrations.AlterModelOptions(
            name='river',
            options={'verbose_name': '河流', 'verbose_name_plural': '河流信息'},
        ),
        migrations.AlterModelOptions(
            name='section',
            options={'verbose_name': '断面', 'verbose_name_plural': '断面信息'},
        ),
    ]