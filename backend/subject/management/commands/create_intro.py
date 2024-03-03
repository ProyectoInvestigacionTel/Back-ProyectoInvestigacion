from django.core.management.base import BaseCommand
from institution.models import Institution
from subject.models import Subject


class Command(BaseCommand):
    help = "Crea TEL-101"

    def handle(self, *args, **kwargs):
        # Aquí colocas la lógica para crear tu usuario
        # Por ejemplo, crear un superusuario:
        if not Subject.objects.filter(name="TEL-101").exists():
            institution_id = Institution.objects.get(
                name="Universidad Técnica Federico Santa María"
            )
            Subject.objects.create(
                name="TEL-101",
                description="Iniciacion a la programación",
                contents="Iteraciones,Bucles,Condicionales",
                institution=institution_id,
            )

            self.stdout.write(self.style.SUCCESS("TEL-101 creado exitosamente"))
        else:
            self.stdout.write(self.style.WARNING("TEL-101 ya existe"))
