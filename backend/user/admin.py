from django.contrib import admin
from .models import CustomUser, Rol, Teacher, Student
from unfold.admin import ModelAdmin


class CustomUserAdmin(ModelAdmin):
    list_display = (
        "user_id",
        "email",
        "name",
        "is_active",
        "is_staff",
        "is_superuser",
        "coins",
    )
    search_fields = ("email", "name")
    list_filter = ("is_active", "is_staff", "is_superuser")
    fieldsets = (
        (None, {"fields": ("user_id", "email", "name", "password")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "roles")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "user_id",
                    "email",
                    "name",
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
    list_display = ("name",)
    search_fields = ("name",)


class TeacherAdmin(admin.ModelAdmin):
    list_display = ("user", "get_subject")
    search_fields = ("user__name", "subject__name")

    def get_subject(self, obj):
        return obj.subject_info.get("subject", "N/A")

    get_subject.short_description = "Subject"


class StudentAdmin(admin.ModelAdmin):
    list_display = ("user", "get_subject", "get_section", "get_semester")
    search_fields = ("user__name", "subject__name")

    def get_section(self, obj):
        return obj.subject_info.get("section", "N/A")

    get_section.short_description = "Section"

    def get_semester(self, obj):
        return obj.subject_info.get("semester", "N/A")

    get_semester.short_description = "Semester"

    def get_subject(self, obj):
        return obj.subject_info.get("subject", "N/A")

    get_subject.short_description = "Subject"


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Rol, RolAdmin)
admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Student, StudentAdmin)
