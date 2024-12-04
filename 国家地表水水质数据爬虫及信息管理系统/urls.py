"""
URL configuration for 国家地表水水质数据爬虫及信息管理系统 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.views.generic import RedirectView

urlpatterns = [
    # 重定向根URL到admin页面
    path('', RedirectView.as_view(url='/admin/', permanent=False)),
    path('admin/', admin.site.urls),
    path('gp/', include('gp.urls')),
    # path('background/', include('background.urls'))

]
#
# urlpatterns += [
#     path('', RedirectView.as_view(url='/gp/', permanent=True))
# ]
# urlpatterns += [
#     path('', RedirectView.as_view(url='/background/', permanent=True))
# ]
