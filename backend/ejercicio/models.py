from django.db import models
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os


def codigo_directory_path(instance, filename):
    return "intento_por_usuario/{0}/{1}/{2}/codigo_Re{2}_Ej{1}.txt".format(
        instance.id_intento.id_intento_general.id_usuario.email,
        instance.id_intento.id_intento_general.id_ejercicio.id_ejercicio,
        instance.id_retroalimentacion,
    )


def conversacion_directory_path(instance, filename):
    return "intento_por_usuario/{0}/{1}/{2}/conversacion_Re{2}_Ej{1}.json".format(
        instance.id_intento.id_intento_general.id_usuario.email,
        instance.id_intento.id_intento_general.id_ejercicio.id_ejercicio,
        instance.id_retroalimentacion,
    )


def resultado_casos_de_uso_directory_path(instance, filename):
    return "intento_por_usuario/{0}/{1}/{2}/resultado_casos_de_uso_Re{2}_Ej{1}.json".format(
        instance.id_intento.id_intento_general.id_usuario.email,
        instance.id_intento.id_intento_general.id_ejercicio.id_ejercicio,
        instance.id_retroalimentacion,
    )


def enunciado_directory_path(instance, filename):
    return "ejercicios/temp/enunciado_{0}".format(filename)


def casos_de_uso_directory_path(instance, filename):
    return "ejercicios/temp/casos_de_uso_{0}".format(filename)


class Ejercicio(models.Model):
    class Meta:
        db_table = "ejercicios"

    id_ejercicio = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    enunciado_file = models.FileField(upload_to=enunciado_directory_path)
    casos_de_uso_file = models.FileField(upload_to=casos_de_uso_directory_path)
    dificultad = models.CharField(max_length=100)
    contenidos = models.CharField(max_length=100)
    puntaje = models.PositiveSmallIntegerField()
    lenguaje = models.CharField(max_length=20)
    asignatura = models.CharField(max_length=30)

    def __str__(self):
        return str(self.id_ejercicio)

    def save(self, *args, **kwargs):
        if not self.pk:
            super(Ejercicio, self).save(*args, **kwargs)

        # movimiento de archivos
        paths_to_update = {}
        for field, prefix in [
            ("enunciado_file", "enunciado_"),
            ("casos_de_uso_file", "casos_de_uso_"),
        ]:
            file_field = getattr(self, field)
            if not file_field:
                continue

            with file_field.open() as f:
                content = ContentFile(f.read())

            temp_path = file_field.path

            # extensión del archivo
            file_extension = os.path.splitext(file_field.name)[1]

            # nombre para el archivo.
            desired_filename = prefix + str(self.id_ejercicio) + file_extension
            new_directory = "ejercicios/{0}/".format(self.id_ejercicio)
            new_path = os.path.join(new_directory, desired_filename)

            # se mueve el archivo.
            default_storage.save(new_path, content)

            try:
                # se intenta eliminar el archivo temporal
                default_storage.delete(temp_path)
            except Exception as e:
                print(f"Error al eliminar el archivo temporal: {e}")

            # almacena la nueva ruta para actualizarla luego.
            paths_to_update[field] = new_path

        # se actualiza a partir de la pk
        Ejercicio.objects.filter(pk=self.pk).update(**paths_to_update)


class IntentoEjercicio(models.Model):
    class Meta:
        db_table = "intentos"

    id_intento_general = models.AutoField(primary_key=True)
    id_ejercicio = models.ForeignKey(
        Ejercicio, on_delete=models.CASCADE, db_column="id_ejercicio"
    )
    id_usuario = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, db_column="id_usuario"
    )
    intentos = models.PositiveSmallIntegerField(default=0)
    nota = models.PositiveSmallIntegerField(default=0)
    tiempo = models.CharField(max_length=20)
    resuelto = models.BooleanField(default=False)


class DetalleIntento(models.Model):
    class Meta:
        db_table = "detalle_intentos"

    id_intento = models.AutoField(primary_key=True)
    id_intento_general = models.ForeignKey(
        IntentoEjercicio, on_delete=models.CASCADE, db_column="id_intento_general"
    )

    fecha = models.DateTimeField()
    nota = models.PositiveSmallIntegerField()
    resuelto = models.BooleanField()
    retroalimentacion = models.PositiveSmallIntegerField()


class DetalleRetroalimentacion(models.Model):
    class Meta:
        db_table = "detalle_retroalimentacion"

    id_retroalimentacion = models.AutoField(primary_key=True)
    id_intento = models.ForeignKey(
        DetalleIntento, on_delete=models.CASCADE, db_column="id_intento"
    )
    conversacion_file = models.FileField(
        upload_to=conversacion_directory_path, null=True, blank=True
    )
    codigo_file = models.FileField(
        upload_to=codigo_directory_path, null=True, blank=True
    )
    resultado_file = models.FileField(
        upload_to=resultado_casos_de_uso_directory_path, null=True, blank=True
    )
    estrellas = models.PositiveSmallIntegerField(default=0)
