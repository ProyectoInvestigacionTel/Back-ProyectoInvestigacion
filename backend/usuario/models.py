from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class Rol(models.Model):
    ESTUDIANTE = "ESTUDIANTE"
    PROFESOR = "PROFESOR"
    ADMIN = "ADMIN"
    AYUDANTE = "AYUDANTE"
    COORDINADOR = "COORDINADOR"

    ROL_OPCIONES = (
        (ESTUDIANTE, "Estudiante"),
        (PROFESOR, "Profesor"),
        (ADMIN, "Administrador"),
        (AYUDANTE, "Ayudante"),
        (COORDINADOR, "Coordinador"),
    )

    nombre = models.CharField(max_length=50, choices=ROL_OPCIONES, unique=True)
    descripcion = models.TextField()

    def __str__(self):
        return self.nombre


class UsuarioPersonalizadoManager(BaseUserManager):
    def create_user(self, id_usuario, email, nombre, password=None):
        if UsuarioPersonalizado.objects.filter(id_usuario=id_usuario).exists():
            raise ValueError("Un usuario con este id_usuario ya existe")
        if not email:
            raise ValueError("El campo email debe estar configurado")
        if not password:
            raise ValueError("El campo password debe estar configurado")

        email = self.normalize_email(email)
        user = self.model(email=email, nombre=nombre, id_usuario=id_usuario)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, id_usuario, email, nombre, password=None):
        admin_role = Rol.objects.get(nombre=Rol.ADMIN)

        user = self.create_user(id_usuario, email, nombre, password)
        user.roles.add(admin_role)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class UsuarioPersonalizado(AbstractBaseUser):
    class Meta:
        db_table = "usuarios"

    id_usuario = models.CharField(primary_key=True, max_length=20, unique=True)
    email = models.EmailField(unique=True, null=True)
    nombre = models.CharField(max_length=50, null=True)
    last_login = models.DateTimeField(db_column="ultimo_acceso", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    roles = models.ManyToManyField(Rol)
    objects = UsuarioPersonalizadoManager()
    monedas = models.SmallIntegerField(default=0)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["nombre", "id_usuario"]

    def has_perms(self, perm, obj=None):
        return self.is_superuser

    def has_perm(self, perm, obj=None):
        return self.is_superuser

    def has_module_perms(self, app_label):
        return self.is_superuser

    def __str__(self):
        return self.email


# Modelo de profesor,ayudante y coordinador
class Docente(models.Model):
    usuario = models.ForeignKey(
        UsuarioPersonalizado, on_delete=models.CASCADE, db_column="id_usuario"
    )
    asignatura = models.CharField(max_length=150)


# Modelo de estudiante
class Estudiante(models.Model):
    usuario = models.ForeignKey(
        UsuarioPersonalizado, on_delete=models.CASCADE, db_column="id_usuario"
    )
    asignatura = models.CharField(max_length=150)
    paralelo = models.CharField(max_length=10)
    semestre = models.CharField(max_length=10)
