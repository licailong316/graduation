from django.urls import path
from gp import views

urlpatterns = [
    # path('', views.index, name='index'),
    path('home_page/', views.home_page, name='home_page'),
    path('crawler/', views.previous_crawler, name='previous_crawler'),
    path('start_crawler/', views.crawler_data, name='crawler_data'),
    path('upload/', views.upload, name='upload'),
    path('date_export/', views.date_export, name='date_export'),
    path('basin_export/', views.basin_export, name='basin_export'),
    path('section_export/', views.section_export, name='section_export'),
    path('river_export/', views.river_export, name='river_export'),
    path('statistic/', views.statistic, name='statistic'),
    path('city_statistic/', views.city_statistic, name='city_statistic'),
    path('get_cities_by_province/', views.get_cities_by_province, name='get_cities_by_province'),
    path('section_statistic/', views.section_statistic, name='section_statistic'),
]
