from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Rol


def create_roles(sender, **kwargs):
    for name, label in Rol.OPTIONS:
        Rol.objects.get_or_create(name=name)
