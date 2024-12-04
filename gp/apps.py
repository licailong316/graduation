from django.apps import AppConfig
from django.contrib.auth.context_processors import auth


class GpConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gp'

    verbose_name = '数据管理'



class YourAppConfig(AppConfig):
    name = 'gp'

    def ready(self):
        from . import tasks
        tasks.start()
