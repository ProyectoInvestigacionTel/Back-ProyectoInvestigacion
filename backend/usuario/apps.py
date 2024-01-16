from django.apps import AppConfig
from django.db.models.signals import post_migrate



class UsuarioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "usuario"
    def ready(self):
        from django.db.models.signals import post_migrate
        from usuario.signals import crear_roles
        post_migrate.connect(crear_roles, sender=self)