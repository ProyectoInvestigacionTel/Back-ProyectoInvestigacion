from django.contrib import admin
from .models import UsuarioPersonalizado, Rol, Docente, Estudiante
from unfold.admin import ModelAdmin


class UsuarioPersonalizadoAdmin(ModelAdmin):
    list_display = (
        "id_usuario",
        "email",
        "nombre",
        "is_active",
        "is_staff",
        "is_superuser",
        "monedas",
    )
    search_fields = ("email", "nombre")
    list_filter = ("is_active", "is_staff", "is_superuser")
    fieldsets = (
        (None, {"fields": ("id_usuario", "email", "nombre", "password")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "roles")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "id_usuario",
                    "email",
                    "nombre",
                    "password",
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "roles",
                ),
            },
        ),
    )

    ordering = ("email",)

    def save_model(self, request, obj, form, change):
        # Si el objeto tiene un atributo 'password' y no está cifrado, cifrarlo
        if hasattr(obj, "password") and not obj.password.startswith(
            ("pbkdf2_sha256$", "bcrypt")
        ):
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)


class RolAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    search_fields = ("nombre",)


class DocenteAdmin(admin.ModelAdmin):
    list_display = ("usuario", "asignatura")
    search_fields = ("usuario__nombre", "asignatura")


class EstudianteAdmin(admin.ModelAdmin):
    list_display = ("usuario", "asignatura", "paralelo", "semestre")
    search_fields = ("usuario__nombre", "asignatura", "paralelo", "semestre")


admin.site.register(UsuarioPersonalizado, UsuarioPersonalizadoAdmin)
admin.site.register(Rol, RolAdmin)
admin.site.register(Docente, DocenteAdmin)
admin.site.register(Estudiante, EstudianteAdmin)
