import json
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


def ejemplo_directory_path(instance, filename):
    return "ejercicios/temp/ejemplo_{0}".format(filename)


def salida_directory_path(instance, filename):
    return "ejercicios/temp/salida_{0}".format(filename)

class Ejercicio(models.Model):
    class Meta:
        db_table = "ejercicios"

    id_ejercicio = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    enunciado_file = models.FileField(upload_to=enunciado_directory_path)
    casos_de_uso_file = models.FileField(upload_to=casos_de_uso_directory_path)
    ejemplo_file = models.FileField(upload_to=ejemplo_directory_path, null=True)
    salida_file = models.FileField(upload_to=salida_directory_path, null=True)
    dificultad = models.CharField(max_length=100)
    contenidos = models.CharField(max_length=100, null=True)
    puntaje = models.PositiveSmallIntegerField(default=0)
    lenguaje = models.CharField(max_length=20)
    asignatura = models.CharField(max_length=30)
    titulo = models.CharField(max_length=100)
    head = models.CharField(max_length=100, null=True)
    tail = models.CharField(max_length=100, null=True)
    binary = models.BooleanField(default=False)
    restricciones = models.TextField()
    formato_entrada = models.TextField()
    formato_salida = models.TextField()
    dependencia_ejercicio = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    visible = models.BooleanField(default=False)
    def __str__(self):
        return str(self.id_ejercicio)

    def save(self, *args, **kwargs):
        enunciado_text = kwargs.pop('enunciado_text', None)
        casos_de_uso = kwargs.pop('casos_de_uso', None)
        super(Ejercicio, self).save(*args, **kwargs)
        
        if enunciado_text:
            # Generate the path and save the enunciado_file.txt
            enunciado_filename = f"enunciado_{self.id_ejercicio}.txt"
            enunciado_path = os.path.join("ejercicios", str(self.id_ejercicio), enunciado_filename)
            default_storage.save(enunciado_path, ContentFile(enunciado_text))
            self.enunciado_file = enunciado_path 
        if casos_de_uso:
            # Generate the path and save the casos_de_uso_file.json
            casos_de_uso_filename = f"casos_de_uso_{self.id_ejercicio}.json"
            casos_de_uso_path = os.path.join("ejercicios", str(self.id_ejercicio), casos_de_uso_filename)
            default_storage.save(casos_de_uso_path, ContentFile(json.dumps(casos_de_uso, indent=4)))
            self.casos_de_uso_file = casos_de_uso_path 
            
        super(Ejercicio, self).save(update_fields=['enunciado_file', 'casos_de_uso_file'])


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
