from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path("docente", UsuarioViewPOSTdocente.as_view(), name="post_profesor"),
    path("estudiante", UsuarioViewPOSTestudiante.as_view(), name="post_estudiante"),
    path("<str:email>", UsuarioViewGET.as_view(), name="get_usuario"),
    # login con jwt
    path("token/", csrf_exempt(LoginUser.as_view()), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
