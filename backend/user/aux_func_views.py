import random
import string
from institution.models import Institution
from datetime import datetime

from user.models import CustomUser, Rol, Student, Teacher
from django.contrib.auth import get_user_model


def generate_random_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = "".join(random.choice(characters) for i in range(length))
    return password


def get_campus_usm(section):
    section = int(section)
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
    context_label = data.get("context_label")
    subject = context_label.split("_")[3]
    context_title = data.get("context_title")

    sections = [
        section.strip() for section in context_title.split("Paralelos:")[1].split(",")
    ]

    subject_info = {"subject": subject, "sections": sections}
    institution, _ = Institution.objects.get_or_create(
        name="Universidad Técnica Federico Santa María"
    )
    user, created = CustomUser.objects.get_or_create(
        user_id=user_id,
        defaults={
            "email": email,
            "name": name,
            "password": generate_random_password(),
            "institution": institution,
            "subject": subject_info,
            "campus": get_campus_usm(sections[0]),
        },
    )
    current_year = datetime.now().year
    semester_half = "1" if datetime.now().month < 7 else "2"
    semester = f"{current_year}-{semester_half}"
    if "Instructor" in roles:
        user.roles.add(Rol.objects.get(name=Rol.Teacher))
        Teacher.objects.update_or_create(user=user)
    elif "Learner" in roles:
        user.roles.add(Rol.objects.get(name=Rol.Student))
        Student.objects.update_or_create(
            user=user,
            defaults={"semester": semester},
        )

    user.save()

    return user
