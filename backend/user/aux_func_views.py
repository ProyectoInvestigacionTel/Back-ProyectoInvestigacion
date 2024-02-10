import random
import string
from institution.models import Institution

from user.models import CustomUser, Rol, Student, Teacher


def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = "".join(random.choice(characters) for i in range(length))
    return password


def get_campus_usm(section):
    if 1 <= section <= 50:
        return "Casa Central Valparaíso"
    elif 100 <= section <= 150:
        return "Santiago Vitacura"
    elif 200 <= section <= 250:
        return "Santiago San Joaquín"
    else:
        return "No campus"


def authenticate_or_create_user(data):
    user_id = data.get("lis_person_sourcedid")
    email = data.get("ext_user_username")
    name = data.get("lis_person_name_full")
    roles = data.get("roles")

    institution_id = Institution.objects.get(
        name="Universidad Técnica Federico Santa María"
    )
    user, created = CustomUser.objects.get_or_create(
        user_id=user_id,
        email=email,
        name=(" ".join((name.split("+")))),
        password=generate_random_password(),
        institution=institution_id,
    )

    # Si el usuario fue creado, asignarle un rol y otros details
    if created:
        # Mapear el valor del campo "roles" del JSON a un rol en la base de datos
        if roles == "Instructor":
            rol = Rol.objects.get(name=Rol.Teacher)
        elif roles == "Learner":
            rol = Rol.objects.get(name=Rol.Student)

        if rol:
            user.roles.add(rol)

        # Crear un perfil adicional para el usuario basado en su rol
        context_label = data.get("context_label")
        subject = context_label.split("_")[3]

        if rol.name == Rol.Student:
            context_title = data.get("context_title")
            print("CONTEXT TITLE:", context_title.split("sections:"))
            section = context_title.split("Paralelos:")[1]
            semester = context_label.split("_")[0]
            subject_info = {
                "subject": subject,
                "section": section,
            }
            CustomUser.objects.filter(user_id=user_id).update(
                campus=get_campus_usm(section)
            )
            Student.objects.create(
                user=user,
                subject=subject_info,
                semester=semester,
            )
        elif rol.name == Rol.Teacher:
            subject_info = {
                subject: subject,
            }
            Teacher.objects.create(user=user, subject=subject)

    return user
