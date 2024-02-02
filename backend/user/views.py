from teloprogramo.settings import SECRET_KEY
from .aux_func_views import generate_random_password
from .models import CustomUser, Teacher, Student, Rol
from .serializers import (
    CustomTokenObtainSerializer,
    StudentPOSTSerializer,
    TeacherPOSTSerializer,
    StudentGETSerializer,
    TeacherGETSerializer,
    CustomUserGETSerializer,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import Http404
from drf_yasg.utils import swagger_auto_schema
from rest_framework_simplejwt.tokens import RefreshToken
from .backend import authenticateUser
from rest_framework import status
from rest_framework.parsers import JSONParser, FormParser
from django.db import transaction
from django.shortcuts import redirect
import jwt


class PostStudentView(APIView):
    @swagger_auto_schema(request_body=StudentPOSTSerializer)
    def post(self, request, *args, **kwargs):
        serializer = StudentPOSTSerializer(data=request.data)
        if serializer.is_valid():
            usuario_data = serializer.validated_data.get("usuario")
            try:
                usuario = CustomUser.objects.create_user(
                    user_id=usuario_data["user_id"],
                    email=usuario_data["email"],
                    name=usuario_data["name"],
                    password=usuario_data["password"],
                    institution=usuario_data["institution"],
                )
                rol_Student = Rol.objects.get(name=Rol.Student)
                usuario.roles.add(rol_Student)

                Student.objects.create(
                    usuario=usuario,
                    subject=serializer.validated_data["subject"],
                    section=serializer.validated_data["section"],
                    semester=serializer.validated_data["semester"],
                )
                return Response(
                    {"message": "Student creado correctamente"},
                    status=status.HTTP_201_CREATED,
                )

            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PostTeacherView(APIView):
    @swagger_auto_schema(request_body=TeacherPOSTSerializer)
    def post(self, request, *args, **kwargs):
        usuario_data = request.data.get("usuario")
        roles_usuario = usuario_data.get("roles")

        roles_permitidos = ["Teacher", "TeacherAssistant", "Coordinator"]
        if any(rol in roles_permitidos for rol in roles_usuario):
            serializer = TeacherPOSTSerializer(data=request.data)
        else:
            return Response(
                {"error": "Rol de usuario no válido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if serializer.is_valid():
            usuario_data = serializer.validated_data.pop("usuario")
            usuario = CustomUser.objects.create_user(
                user_id=usuario_data["rol_usm"],
                email=usuario_data["email"],
                name=usuario_data["name"],
                password=usuario_data["password"],
                institution=usuario_data["institution"],
            )

            for rol_name in roles_usuario:
                rol_obj = Rol.objects.get(name=rol_name)
                usuario.roles.add(rol_obj)

            Teacher.objects.create(
                usuario=usuario,
                subject=serializer.validated_data["subject"],
            )

            return Response(
                {"message": "Teacher creado correctamente"},
                status=status.HTTP_201_CREATED,
                data=None,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class UserView(APIView):
    def get(self, request, email, *args, **kwargs):
        try:
            usuario = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            raise Http404

        if (
            usuario.roles.filter(name="Teacher").exists()
            or usuario.roles.filter(name="TeacherAssistant").exists()
            or usuario.roles.filter(name="Coordinator").exists()
        ):
            serializer = TeacherGETSerializer(usuario.Teacher)
        elif usuario.roles.filter(name="Student").exists():
            serializer = StudentGETSerializer(usuario.Student)
        elif usuario.roles.filter(name="ADMIN").exists():
            serializer = CustomUserGETSerializer(usuario)
        else:
            return Response(
                {"error": "Rol de usuario no válido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(serializer.data, status=status.HTTP_200_OK)


class LoginUser(APIView):
    parser_classes = [FormParser, JSONParser]

    @transaction.atomic
    @swagger_auto_schema(request_body=CustomTokenObtainSerializer)
    def post(self, request):
        print("FORM:", request.data)
        email = request.data.get("email")
        password = request.data.get("password")

        if email and password:
            print("user found", flush=True)
            user = authenticateUser(email=email, password=password)
            if not user:
                return Response(
                    {
                        "error": "No se pudo autenticar con las credenciales proporcionadas."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            email = request.data.get("ext_user_username")
            # Si no se proporcionaron email y password, usar la función para autenticar o crear el usuario
            user = CustomUser.objects.filter(email=email).exists()

            if not user:
                user = authenticate_or_create_user(request.data)
            else:
                user = CustomUser.objects.get(email=email)

        user_serializer = CustomUser.objects.get(email=user.email)

        user_data = {
            "user_id": user_serializer.user_id,
            "email": user_serializer.email,
            "name": user_serializer.name,
            "roles": [rol.name for rol in user_serializer.roles.all()],
        }

        refresh = RefreshToken.for_user(user)
        refresh = jwt.decode(str(refresh), SECRET_KEY, algorithms=["HS256"])
        refresh["user_data"] = user_data
        refresh = jwt.encode(refresh, SECRET_KEY, algorithm="HS256")
        return redirect("http://localhost:3000/auth?token=" + str(refresh))
        #return redirect("https://teloprogramo.cl/auth?token=" + str(refresh))


class LoginUserToken(APIView):
    parser_classes = [JSONParser]

    @transaction.atomic
    @swagger_auto_schema(request_body=CustomTokenObtainSerializer)
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if email and password:
            user = authenticateUser(email=email, password=password)
            if not user:
                return Response(
                    {
                        "error": "No se pudo autenticar con las credenciales proporcionadas."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            email = request.data.get("ext_user_username")
            # Si no se proporcionaron email y contraseña, usar la función para autenticar o crear el usuario
            user = CustomUser.objects.filter(email=email).exists()

            if not user:
                user = authenticate_or_create_user(request.data)
            else:
                user = CustomUser.objects.get(email=email)

        refresh = RefreshToken.for_user(user)
        token_data = {"access": str(refresh.access_token), "refresh": str(refresh)}

        user_serializer = CustomUser.objects.get(email=user.email)
        print((user_serializer.__dict__), flush=True)

        user_data = {
            "user_id": user_serializer.user_id,
            "email": user_serializer.email,
            "name": user_serializer.name,
            "roles": [rol.name for rol in user_serializer.roles.all()],
        }

        response_data = {**user_data, **token_data}
        return Response(response_data, status=status.HTTP_200_OK)


def authenticate_or_create_user(data):
    user_id = data.get("lis_person_sourcedid")
    email = data.get("ext_user_username")
    name = data.get("lis_person_name_full")
    roles = data.get("roles")

    user, created = CustomUser.objects.get_or_create(
        user_id=user_id,
        email=email,
        name=(" ".join((name.split("+")))),
        password=generate_random_password(),
        institution="USM",
    )

    # Si el usuario fue creado, asignarle un rol y otros details
    if created:
        # Mapear el valor del campo "roles" del JSON a un rol en la base de datos
        if roles == "Instructor":
            rol = Rol.objects.get(name=Rol.Teacher)
        elif roles == "Learner":
            rol = Rol.objects.get(name=Rol.Student)

        if rol:
            user.roles.add(rol)

        # Crear un perfil adicional para el usuario basado en su rol
        context_label = data.get("context_label")
        subject = context_label.split("_")[3]

        if rol.name == Rol.Student:
            context_title = data.get("context_title")
            print("CONTEXT TITLE:", context_title.split("sections:"))
            section = context_title.split("Paralelos:")[1]
            semester = context_label.split("_")[0]
            Student.objects.create(
                user=user,
                subject=subject,
                section=section,
                semester=semester,
            )
        elif rol.name == Rol.Teacher:
            Teacher.objects.create(user=user, subject=subject)

    return user
