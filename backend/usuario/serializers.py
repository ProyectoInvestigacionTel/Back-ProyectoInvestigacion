from rest_framework import serializers
from .models import *


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ("nombre",)


class UsuarioPersonalizadoPOSTSerializer(serializers.ModelSerializer):
    roles = RolSerializer(many=True)

    class Meta:
        model = UsuarioPersonalizado
        fields = ("email", "nombre", "roles", "password")


class UsuarioPersonalizadoGETSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = UsuarioPersonalizado
        fields = ("id_usuario", "email", "nombre", "roles")

    def get_roles(self, obj):
        return ", ".join([rol.nombre for rol in obj.roles.all()])


class DocentePOSTSerializer(serializers.ModelSerializer):
    usuario = UsuarioPersonalizadoPOSTSerializer()

    class Meta:
        model = Docente
        fields = ("usuario", "asignatura")


class DocenteGETSerializer(serializers.ModelSerializer):
    usuario = UsuarioPersonalizadoGETSerializer()

    class Meta:
        model = Docente
        fields = ("usuario", "asignatura")


class EstudiantePOSTSerializer(serializers.ModelSerializer):
    usuario = UsuarioPersonalizadoPOSTSerializer()

    class Meta:
        model = Estudiante
        fields = ("usuario", "asignatura", "paralelo", "semestre")


class EstudianteGETSerializer(serializers.ModelSerializer):
    usuario = UsuarioPersonalizadoGETSerializer()

    class Meta:
        model = Estudiante
        fields = ("usuario", "asignatura", "paralelo", "semestre")


class CustomTokenObtainSerializer(serializers.Serializer):
    email = serializers.EmailField()
    contrasena = serializers.CharField(write_only=True)
