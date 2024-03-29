from django.core.management.base import BaseCommand
from user.models import CustomUser
from user.utils import generate_avatar_url
from django.db.models import Q


class Command(BaseCommand):
    help = "Actualiza los avatares de los usuarios sin imagen de perfil"

    def handle(self, *args, **kwargs):
        users_without_picture = CustomUser.objects.filter(Q(picture__isnull=True) | Q(picture__exact=""))

        for user in users_without_picture:
            user.picture = generate_avatar_url(user.name)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f"Avatar actualizado para {user.email}")
            )
