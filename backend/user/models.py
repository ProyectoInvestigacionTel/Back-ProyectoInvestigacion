from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models

from user.utils import generate_avatar_url


class Rol(models.Model):
    Student = "Student"
    Teacher = "Teacher"
    ADMIN = "ADMIN"
    TeacherAssistant = "TeacherAssistant"
    Coordinator = "Coordinator"

    OPTIONS = (
        (Student, "Student"),
        (Teacher, "Teacher"),
        (ADMIN, "Administrador"),
        (TeacherAssistant, "TeacherAssistant"),
        (Coordinator, "Coordinator"),
    )

    name = models.CharField(max_length=50, choices=OPTIONS)

    def __str__(self):
        return self.name


class CustomUserManager(BaseUserManager):
    def create_user(self, user_id, email, name, institution, campus,subject, password=None):
        if CustomUser.objects.filter(user_id=user_id).exists():
            raise ValueError("Un usuario con este user_id ya existe")
        if not email:
            raise ValueError("El campo email debe estar configurado")
        if not password:
            raise ValueError("El campo password debe estar configurado")

        email = self.normalize_email(email)
        user = self.model(email=email, name=name, user_id=user_id)
        user.set_password(password)
        user.campus = campus
        user.subject = subject
        user.institution = institution
        user.save(using=self._db)
        return user

    def create_superuser(
        self, user_id, email, name, institution, campus,subject, password=None
    ):
        admin_role = Rol.objects.get(name=Rol.ADMIN)

        user = self.create_user(user_id, email, name, institution, campus,subject, password)
        user.roles.add(admin_role)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class CustomUser(AbstractBaseUser):
    class Meta:
        db_table = "user"

    user_id = models.CharField(primary_key=True, max_length=20, unique=True)
    email = models.EmailField(unique=True, null=True)
    name = models.CharField(max_length=50, null=True)
    last_login = models.DateTimeField(db_column="Last_acceso", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    roles = models.ManyToManyField(Rol)
    objects = CustomUserManager()
    coins = models.SmallIntegerField(default=0)
    institution = models.ForeignKey(
        "institution.Institution",
        on_delete=models.DO_NOTHING,
        db_column="institution",
        null=True,
        blank=True,
    )
    campus = models.CharField(max_length=100, null=True)
    picture = models.ImageField(upload_to="user_photos/", null=True, blank=True)
    subject = models.JSONField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "user_id"]

    def has_perms(self, perm, obj=None):
        return self.is_superuser

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.picture:
            self.picture = generate_avatar_url(self.email)
        super(CustomUser, self).save(*args, **kwargs)


# Modelo de Teacher,TeacherAssistant y Coordinator
class Teacher(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, db_column="user_id")


# Modelo de Student
class Student(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, db_column="user_id")
    semester = models.CharField(max_length=10)
