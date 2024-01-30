from django.apps import AppConfig
from django.db.models.signals import post_migrate



class UserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "user"
    def ready(self):
        from django.db.models.signals import post_migrate
        from user.signals import create_roles
        post_migrate.connect(create_roles, sender=self)