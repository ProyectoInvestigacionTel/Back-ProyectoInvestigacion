from django.core.management.base import BaseCommand
from usuario.models import UsuarioPersonalizado, Rol

class Command(BaseCommand):
    help = 'Crea un usuario personalizado'

    def handle(self, *args, **kwargs):
        # Aquí colocas la lógica para crear tu usuario
        # Por ejemplo, crear un superusuario:
        if not UsuarioPersonalizado.objects.filter(email="admin@usm.cl").exists():
            UsuarioPersonalizado.objects.create_superuser(
                id_usuario="02",
                email="admin@usm.cl",
                nombre="Admin",
                password="admin"
            )
            self.stdout.write(self.style.SUCCESS('Superusuario creado exitosamente'))
        else:
            self.stdout.write(self.style.WARNING('El superusuario ya existe'))
