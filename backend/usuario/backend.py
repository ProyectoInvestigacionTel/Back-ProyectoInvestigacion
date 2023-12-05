from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from .models import UsuarioPersonalizado as usuario


def authenticateUser(email, password):
    try:
        user = usuario.objects.get(email=email)
        if user and check_password(password, user.password) is True:
            return user
    except usuario.DoesNotExist:
        pass
    return None
