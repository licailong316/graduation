"""
ASGI config for 国家地表水水质数据爬虫及信息管理系统 project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', '国家地表水水质数据爬虫及信息管理系统.settings')

application = get_asgi_application()
