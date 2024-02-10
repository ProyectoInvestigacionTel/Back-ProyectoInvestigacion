from django.core.management.base import BaseCommand
from institution.models import Institution
from subject.models import Subject
from user.models import CustomUser, Rol, Student


class Command(BaseCommand):
    help = "Crea un usuario personalizado"

    def handle(self, *args, **kwargs):
        if not CustomUser.objects.filter(email="admin@usm.cl").exists():
            institution_id = Institution.objects.get(
                name="Universidad Técnica Federico Santa María"
            )
            subject = {
                "subject": "TEL-101",
                "section": "200",
            }
            CustomUser.objects.create_superuser(
                user_id="02",
                email="admin@usm.cl",
                name="Admin",
                password="admin",
                institution=institution_id,
                campus="Santiago San Joaquín",
            )
            CustomUser.objects.create_user(
                user_id="01",
                email="test@usm.cl",
                name="Test",
                password="test",
                institution=institution_id,
                campus="Santiago San Joaquín",
            )
            Student.objects.create(
                user=CustomUser.objects.get(user_id="01"),
                subject=subject,
                semester="2024-1",
            )
            Student.objects.create(
                user=CustomUser.objects.get(user_id="02"),
                subject=subject,
                semester="2024-1",
            )
            self.stdout.write(self.style.SUCCESS("Superusuario creado exitosamente"))
        else:
            self.stdout.write(self.style.WARNING("El superusuario ya existe"))
