from rest_framework import serializers
from .models import *

from django.contrib.auth import get_user_model


class EjercicioSerializerCreate(serializers.ModelSerializer):
    enunciado_file = serializers.FileField(required=True)
    casos_de_uso_file = serializers.FileField(required=True)

    class Meta:
        model = Ejercicio
        fields = (
            "id_ejercicio",
            "fecha",
            "id_usuario",
            "enunciado_file",
            "casos_de_uso_file",
            "dificultad",
            "contenidos",
            "puntaje",
            "lenguaje",
            "asignatura",
        )


class EjercicioSerializerView(serializers.ModelSerializer):
    class Meta:
        model = Ejercicio
        fields = [
            "id_ejercicio",
            "fecha",
            "id_usuario",
            "dificultad",
            "contenidos",
            "puntaje",
            "lenguaje",
        ]


class EjercicioListSerializerAll(serializers.ModelSerializer):
    class Meta:
        model = Ejercicio
        fields = [
            "id_ejercicio",
            "dificultad",
            "puntaje",
            "contenidos",
            "lenguaje",
            "asignatura",
            "id_usuario",
            "nombre_usuario",
            "email_usuario",
        ]


class IntentoEjercicioSerializer(serializers.ModelSerializer):
    id_ejercicio = serializers.PrimaryKeyRelatedField(queryset=Ejercicio.objects.all())
    id_usuario = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all()
    )
    tiempo = serializers.CharField(default="10:00:00")
    codigo = serializers.CharField(default='print("Hello World")', write_only=True)
    feedback_inicial = serializers.CharField(
        default="feedback inicial", write_only=True
    )

    def create(self, validated_data):
        validated_data.pop("codigo", None)
        validated_data.pop("feedback_inicial", None)

        return IntentoEjercicio.objects.create(**validated_data)

    class Meta:
        model = IntentoEjercicio
        fields = ["id_ejercicio", "id_usuario", "tiempo", "codigo", "feedback_inicial"]


class DetalleIntentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleIntento
        fields = "__all__"


class DetalleRetroalimentacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DetalleRetroalimentacion
        fields = "__all__"


class MensajeSerializer(serializers.Serializer):
    remitente = serializers.CharField(max_length=100)
    mensaje = serializers.CharField()


class ConversacionSerializer(serializers.Serializer):
    mensajes = MensajeSerializer(many=True)


