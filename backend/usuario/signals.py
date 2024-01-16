from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import Rol

def crear_roles(sender, **kwargs):
    for nombre, etiqueta in Rol.ROL_OPCIONES:
        Rol.objects.get_or_create(nombre=nombre)
