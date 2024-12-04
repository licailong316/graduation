# Generated by Django 4.2.3 on 2024-05-20 10:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gp', '0008_alter_basin_options_alter_city_options_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='data',
            index=models.Index(fields=['river_id'], name='gp_data_river_i_a9880e_idx'),
        ),
        migrations.AddIndex(
            model_name='data',
            index=models.Index(fields=['province_id'], name='gp_data_provinc_1a7a66_idx'),
        ),
        migrations.AddIndex(
            model_name='data',
            index=models.Index(fields=['city_id'], name='gp_data_city_id_7c303e_idx'),
        ),
        migrations.AddIndex(
            model_name='data',
            index=models.Index(fields=['basin_id'], name='gp_data_basin_i_20bc3d_idx'),
        ),
        migrations.AddIndex(
            model_name='data',
            index=models.Index(fields=['section_id'], name='gp_data_section_eedc19_idx'),
        ),
        migrations.AddIndex(
            model_name='data',
            index=models.Index(fields=['monitoring_time'], name='gp_data_monitor_814d4d_idx'),
        ),
    ]