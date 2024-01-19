from rest_framework import serializers
from .models import *

from django.contrib.auth import get_user_model


class EjercicioSerializerCreate(serializers.ModelSerializer):
    enunciado = serializers.FileField(required=True)
    casos_de_uso = serializers.FileField(required=True)
    ejemplo_file = serializers.FileField(required=False)
    salida_file = serializers.FileField(required=False)
    dificultad = serializers.CharField(required=True)

    class Meta:
        model = Ejercicio
        exclude = [
            "fecha",
        ]


class EjercicioSerializerCreateProfesor(serializers.ModelSerializer):
    title = serializers.CharField(required=True, source="titulo")
    subject = serializers.CharField(required=True, source="asignatura")
    problem_statement = serializers.CharField(required=True, source="enunciado_file")
    constraints = serializers.CharField(required=True, source="restricciones")
    input_format = serializers.CharField(required=True, source="formato_entrada")
    output_format = serializers.CharField(required=True, source="formato_salida")
    id_usuario = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all(),write_only=True
    )
    class Meta:
        model = Ejercicio
        fields = [
            "title",
            "subject",
            "problem_statement",
            "input_format",
            "constraints",
            "output_format",
            "id_usuario",
        ]


class EjercicioSerializerView(serializers.ModelSerializer):
    class Meta:
        model = Ejercicio
        fields = "__all__"


class EjercicioListSerializerAll(serializers.ModelSerializer):
    class Meta:
        model = Ejercicio
        fields = "__all__"


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
