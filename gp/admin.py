from django.contrib import admin
from .models import Province, City, River, Section, Data, Basin
from import_export.admin import ExportActionMixin


# Register your models here.
# class UserAdmin(ExportActionMixin,admin.ModelAdmin):
#     list_display = ['id', 'username', 'password', 'email']
#     ordering = ['id']
#
# admin.site.register(User, UserAdmin)


class ProvinceAdmin(ExportActionMixin,admin.ModelAdmin):
    list_display = ['province_id', 'province_name']
    ordering = ['province_id']

admin.site.register(Province, ProvinceAdmin)


class CityAdmin(ExportActionMixin,admin.ModelAdmin):
    list_display = ['city_id', 'province', 'city_name']
    ordering = ['city_id']

admin.site.register(City, CityAdmin)


class BasinAdmin(ExportActionMixin,admin.ModelAdmin):
    list_display = ['basin_id', 'basin_name']
    ordering = ['basin_id']

admin.site.register(Basin, BasinAdmin)


class RiverAdmin(ExportActionMixin,admin.ModelAdmin):
    list_display = ['river_id', 'basin', 'river_name']
    ordering = ['river_id']

admin.site.register(River, RiverAdmin)


class SectionAdmin(ExportActionMixin,admin.ModelAdmin):
    list_display = ['section_id', 'province',  'city', 'basin', 'river', 'section_name']
    ordering = ['section_id']

admin.site.register(Section, SectionAdmin)


class DataAdmin(ExportActionMixin,admin.ModelAdmin):
    list_display = ['id', 'province', 'city', 'basin', 'river', 'section', 'monitoring_time', 'water_type', 'water_temperature', 'pH',
                    'dissolved_oxygen', 'conductivity', 'turbidity', 'permanganate_index', 'ammonia_nitrogen',
                    'total_phosphorus', 'total_nitrogen', 'chlorophyll_alpha', 'algal_density', 'station_status']
    ordering = ['-monitoring_time']

admin.site.register(Data, DataAdmin)

"""修改SimpleUI 后台管理的名称和标题"""
from django.contrib import admin
admin.site.site_header = '数据爬虫及信息管理系统' # 设置header
admin.site.site_title = '数据爬虫及信息管理系统' # 设置 title





