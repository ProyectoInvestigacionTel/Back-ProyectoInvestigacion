import random
import string
from institution.models import Institution
from datetime import datetime
import pandas as pd
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

    sections_str = context_title.split("Paralelos:")[1]
    sections = sections_str.split("/")

    sections = [section.strip() for section in sections]

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


def read_excel_and_update_users(excel_file):
    df = pd.read_excel(excel_file, header=None, skiprows=8)
    df.columns = [
        "N°",
        "ROL USM",
        "DV",
        "RUT",
        "DV",
        "Ap.Paterno",
        "Ap.Materno",
        "Nombres",
        "VTR",
        "Carrera",
        "Correo",
    ]

    asignatura_info_row = pd.read_excel(
        excel_file, header=None, nrows=1, skiprows=2
    ).iloc[0, 0]
    asignatura_info = str(asignatura_info_row)
    subject_code = asignatura_info.split(":")[1].split("-")[0].strip()

    paralelo_info_row = pd.read_excel(
        excel_file, header=None, nrows=1, skiprows=3
    ).iloc[0, 0]
    section = str(paralelo_info_row).split(":")[1].strip()
    print(f"Subject: {subject_code}, Section: {section}", flush=True)
    for index, student_info in df.iterrows():
        if pd.isnull(student_info["Correo"]):
            continue

        email = student_info["Correo"]
        print(f"Updating user with email {email}", flush=True)
        try:
            user = CustomUser.objects.get(email=email)

            user.subject = {"subject": subject_code, "sections": [section]}
            user.save()
        except CustomUser.DoesNotExist:
            print(f"No se encontró el usuario con email {email}")
