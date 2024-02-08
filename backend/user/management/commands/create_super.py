from django.core.management.base import BaseCommand
from user.models import CustomUser, Rol


class Command(BaseCommand):
    help = "Crea un usuario personalizado"

    def handle(self, *args, **kwargs):
        # Aquí colocas la lógica para crear tu usuario
        # Por ejemplo, crear un superusuario:
        if not CustomUser.objects.filter(email="admin@usm.cl").exists():
            CustomUser.objects.create_superuser(
                user_id="02", email="admin@usm.cl", name="Admin", password="admin"
            )
            CustomUser.objects.create(
                user_id="01", email="test@usm.cl", name="Test", password="test"
            )

            self.stdout.write(self.style.SUCCESS("Superusuario creado exitosamente"))
        else:
            self.stdout.write(self.style.WARNING("El superusuario ya existe"))
