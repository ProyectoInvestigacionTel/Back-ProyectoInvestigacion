from django.urls import path, re_path, include
from rest_framework import routers
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.authentication import TokenAuthentication
from django.contrib.auth.decorators import login_required
from django.contrib import admin
from django.views.decorators.csrf import csrf_exempt

schema_view = get_schema_view(
    openapi.Info(
        url="http://localhost:8001/api",
        title="Tu API",
        default_version="v1",
        description="Descripción de tu API",
        terms_of_service="URL de los términos de servicio",
        contact=openapi.Contact(email="contacto@tu-dominio.com"),
        license=openapi.License(name="Licencia de tu API"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    authentication_classes=(TokenAuthentication,),
)
router = routers.DefaultRouter()

api_urlpatterns = [
    path("user/", include("user.urls")),
    path("exercise/", include("exercise.urls")),
    path("subject/", include("subject.urls")),
    path("institution/", include("institution.urls")),
    path(
        "swagger<format>/", schema_view.without_ui(cache_timeout=0), name="schema-json"
    ),
    path(
        "",
        login_required(schema_view.with_ui("swagger", cache_timeout=0)),
        name="schema-swagger-ui",
    ),
    path(
        "redoc/",
        login_required(schema_view.with_ui("redoc", cache_timeout=0)),
        name="schema-redoc",
    ),
]

admin.site.site_header = "Ir a swagger"
admin.site.site_url = "/api"

urlpatterns = [path("api/", include(api_urlpatterns)), path("admin/", admin.site.urls)]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
