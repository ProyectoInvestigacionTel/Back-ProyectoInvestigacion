from django.core.management.base import BaseCommand
from institution.models import Institution


class Command(BaseCommand):
    help = "Crea la institución USM"

    def handle(self, *args, **kwargs):
        if not Institution.objects.filter(name="Universidad Técnica Federico Santa María").exists():
            campus = {
                "Casa Central": {
                    "address": "Av. España 1680",
                    "city": "Valparaíso",
                    "country": "Chile",
                    "phone": "+56 32 2654000",
                    "website": "https://www.usm.cl",
                    "description": "Universidad Técnica Federico Santa María",
                },
                "Santiago Vitacura": {
                    "address": "Vitacura",
                    "city": "Santiago",
                    "country": "Chile",
                    "phone": "+56 2 2354000",
                    "website": "https://www.usm.cl",
                    "description": "Universidad Técnica Federico Santa María",
                },
                "Santiago San Joaquín": {
                    "address": "Av. Vicuña Mackenna 3939",
                    "city": "Santiago",
                    "country": "Chile",
                    "phone": "+56 2 2354000",
                    "website": "https://www.usm.cl",
                    "description": "Universidad Técnica Federico Santa María",
                },
            }
            Institution.objects.create(
                name="Universidad Técnica Federico Santa María",
                address="Av. España 1680",
                city="Valparaíso",
                country="Chile",
                phone="+56 32 2654000",
                website="https://www.usm.cl",
                description="Universidad Técnica Federico Santa María",
                campus=campus,
            )

            self.stdout.write(self.style.SUCCESS("USM creado exitosamente"))
        else:
            self.stdout.write(self.style.WARNING("La institucion ya existe"))
