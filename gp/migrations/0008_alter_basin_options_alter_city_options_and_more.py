# Generated by Django 4.2.3 on 2024-05-19 10:38

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gp', '0007_delete_user_alter_basin_options_alter_city_options_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='basin',
            options={'verbose_name': '流域', 'verbose_name_plural': '流域数据管理'},
        ),
        migrations.AlterModelOptions(
            name='city',
            options={'verbose_name': '城市', 'verbose_name_plural': '城市数据管理'},
        ),
        migrations.AlterModelOptions(
            name='data',
            options={'verbose_name': '数据', 'verbose_name_plural': '水质数据管理'},
        ),
        migrations.AlterModelOptions(
            name='province',
            options={'verbose_name': '省份', 'verbose_name_plural': '省份数据管理'},
        ),
        migrations.AlterModelOptions(
            name='river',
            options={'verbose_name': '河流', 'verbose_name_plural': '河流数据管理'},
        ),
        migrations.AlterModelOptions(
            name='section',
            options={'verbose_name': '断面', 'verbose_name_plural': '断面数据管理'},
        ),
    ]
