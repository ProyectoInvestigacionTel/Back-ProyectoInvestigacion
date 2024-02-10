from rest_framework import serializers
from .models import *


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ("name",)


class CustomUserPOSTSerializer(serializers.ModelSerializer):
    roles = RolSerializer(many=True)
    rol_usm = serializers.CharField(source="user_id")

    class Meta:
        model = CustomUser
        fields = ("rol_usm", "email", "name", "roles", "password", "institution")


class CustomUserGETSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ("user_id", "email", "name", "roles", "institution")

    def get_roles(self, obj):
        return ", ".join([rol.name for rol in obj.roles.all()])


class TeacherPOSTSerializer(serializers.ModelSerializer):
    usuario = CustomUserPOSTSerializer()
    subject = serializers.JSONField()
    class Meta:
        model = Teacher
        fields = ("usuario", "subject")


class TeacherGETSerializer(serializers.ModelSerializer):
    usuario = CustomUserGETSerializer()
    subject = serializers.JSONField()
    class Meta:
        model = Teacher
        fields = ("usuario", "subject")


class StudentPOSTSerializer(serializers.ModelSerializer):
    usuario = CustomUserPOSTSerializer()
    subject = serializers.JSONField()
    class Meta:
        model = Student
        fields = ("usuario", "subject", "semester")


class StudentGETSerializer(serializers.ModelSerializer):
    usuario = CustomUserGETSerializer()
    subject = serializers.JSONField()   
    class Meta:
        model = Student
        fields = ("usuario", "subject", "semester")


class CustomTokenObtainSerializer(serializers.Serializer):
    email = serializers.EmailField(default="admin@usm.cl")
    password = serializers.CharField(write_only=True, default="admin")
