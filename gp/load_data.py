# import os
# from django.core.management.base import BaseCommand
# from gp.models import Province, City, Basin, River, Section, Data
# import pandas as pd
#
# class Command(BaseCommand):
#     def handle(self, *args, **options):
#         cleaned_csv_folder = r'D:\html\source_csv'
#
#         for file_name in os.listdir(cleaned_csv_folder):
#             if file_name.endswith(".csv"):
#                 cleaned_csv_file = os.path.join(cleaned_csv_folder, file_name)
#                 df = pd.read_csv(cleaned_csv_file)
#
#                 for _, row in df.iterrows():
#                     province, _ = Province.objects.get_or_create(province_name=row['省份'])
#                     city, _ = City.objects.get_or_create(city_name=row['所属地区'], province=province)
#                     basin, _ = Basin.objects.get_or_create(basin_name=row['流域'])
#                     river, _ = River.objects.get_or_create(river_name=row['所属河流'], basin=basin)
#                     section, _ = Section.objects.get_or_create(section_name=row['断面名称'], province=province, city=city, basin=basin, river=river)
#
#                     # 检查是否数据库中已存在相同数据
#                     if not Data.objects.filter(
#                         province=province,
#                         city=city,
#                         basin=basin,
#                         river=river,
#                         section=section,
#                         monitoring_time=row['监测时间']  # 根据实际需要添加其他字段
#                     ).exists():
#                         # 不存在则新建数据
#                         Data.objects.create(
#                             province=province,
#                             city=city,
#                             basin=basin,
#                             river=river,
#                             section=section,
#                             monitoring_time=row['监测时间'],
#                             water_type=row['水质类别'],
#                             water_temperature=row['水温(℃)'],
#                             pH=row['pH(无量纲)'],
#                             dissolved_oxygen=row['溶解氧(mg/L)'],
#                             conductivity=row['电导率(μS/cm)'],
#                             turbidity=row['浊度(NTU)'],
#                             permanganate_index=row['高锰酸盐指数(mg/L)'],
#                             ammonia_nitrogen=row['氨氮(mg/L)'],
#                             total_phosphorus=row['总磷(mg/L)'],
#                             total_nitrogen=row['总氮(mg/L)'],
#                             chlorophyll_alpha=row['叶绿素α(mg/L)'],
#                             algal_density=row['藻密度(cells/L)'],
#                             station_status=row['站点情况']
#                         )
#
#         self.stdout.write(self.style.SUCCESS('数据加载完成！'))