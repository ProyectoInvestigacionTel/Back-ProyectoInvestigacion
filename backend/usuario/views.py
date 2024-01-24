from teloprogramo.settings import SECRET_KEY
from .aux_func_views import generate_random_password
from .models import UsuarioPersonalizado, Docente, Estudiante, Rol
from .serializers import (
    EstudiantePOSTSerializer,
    DocentePOSTSerializer,
    EstudianteGETSerializer,
    DocenteGETSerializer,
    UsuarioPersonalizadoGETSerializer,
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


class UsuarioViewPOSTestudiante(APIView):
    @swagger_auto_schema(request_body=EstudiantePOSTSerializer)
    def post(self, request, *args, **kwargs):
        serializer = EstudiantePOSTSerializer(data=request.data)
        if serializer.is_valid():
            usuario_data = serializer.validated_data.get('usuario')
            try:
                usuario = UsuarioPersonalizado.objects.create_user(
                    id_usuario=usuario_data['id_usuario'],
                    email=usuario_data['email'],
                    nombre=usuario_data['nombre'],
                    password=usuario_data['password'],
                )
                rol_estudiante = Rol.objects.get(nombre=Rol.ESTUDIANTE)
                usuario.roles.add(rol_estudiante)

                Estudiante.objects.create(
                    usuario=usuario,
                    asignatura=serializer.validated_data['asignatura'],
                    paralelo=serializer.validated_data['paralelo'],
                    semestre=serializer.validated_data['semestre'],
                )
                return Response({"message": "Estudiante creado correctamente"}, status=status.HTTP_201_CREATED)

            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsuarioViewPOSTdocente(APIView):
    @swagger_auto_schema(request_body=DocentePOSTSerializer)
    def post(self, request, *args, **kwargs):
        usuario_data = request.data.get("usuario")
        roles_usuario = usuario_data.get("roles")

        roles_permitidos = ["PROFESOR", "AYUDANTE", "COORDINADOR"]
        if any(rol in roles_permitidos for rol in roles_usuario):
            serializer = DocentePOSTSerializer(data=request.data)
        else:
            return Response(
                {"error": "Rol de usuario no válido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if serializer.is_valid():
            usuario_data = serializer.validated_data.pop("usuario")
            usuario = UsuarioPersonalizado.objects.create_user(
                id_usuario=usuario_data["rol_usm"],
                email=usuario_data["email"],
                nombre=usuario_data["nombre"],
                password=usuario_data["password"],
            )

            for rol_nombre in roles_usuario:
                rol_obj = Rol.objects.get(nombre=rol_nombre)
                usuario.roles.add(rol_obj)

            Docente.objects.create(
                usuario=usuario,
                asignatura=serializer.validated_data["asignatura"],
            )

            return Response(
                {"message": "Docente creado correctamente"},
                status=status.HTTP_201_CREATED,
                data=None,
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


class UsuarioViewGET(APIView):
    def get(self, request, email, *args, **kwargs):
        try:
            usuario = UsuarioPersonalizado.objects.get(email=email)
        except UsuarioPersonalizado.DoesNotExist:
            raise Http404

        if (
            usuario.roles.filter(nombre="Profesor").exists()
            or usuario.roles.filter(nombre="Ayudante").exists()
            or usuario.roles.filter(nombre="Coordinador").exists()
        ):
            serializer = DocenteGETSerializer(usuario.docente)
        elif usuario.roles.filter(nombre="Estudiante").exists():
            serializer = EstudianteGETSerializer(usuario.estudiante)
        elif usuario.roles.filter(nombre="ADMIN").exists():
            serializer = UsuarioPersonalizadoGETSerializer(usuario)
        else:
            return Response(
                {"error": "Rol de usuario no válido"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(serializer.data, status=status.HTTP_200_OK)


class LoginUser(APIView):
    parser_classes = [FormParser, JSONParser]

    @transaction.atomic
    def post(self, request):
        print("FORM:",request.data)
        email = request.data.get("email")
        password = request.data.get("contrasena")

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
            user = UsuarioPersonalizado.objects.filter(email=email).exists()

            if not user:
                user = authenticate_or_create_user(request.data)
            else:
                user = UsuarioPersonalizado.objects.get(email=email)

        user_serializer = UsuarioPersonalizado.objects.get(email=user.email)

        user_data = {
            "id_usuario": user_serializer.id_usuario,
            "email": user_serializer.email,
            "nombre": user_serializer.nombre,
            "roles": [rol.nombre for rol in user_serializer.roles.all()],
        }

        refresh = RefreshToken.for_user(user)
        refresh = jwt.decode(str(refresh), SECRET_KEY, algorithms=["HS256"])
        refresh['user_data'] = user_data
        refresh = jwt.encode(refresh, SECRET_KEY, algorithm="HS256")
    
        return redirect("https://teloprogramo.cl/auth?token=" + str(refresh))


def authenticate_or_create_user(data):
    user_id = data.get("lis_person_sourcedid")
    email = data.get("ext_user_username")
    nombre = data.get("lis_person_name_full")
    roles = data.get("roles")

    user, created = UsuarioPersonalizado.objects.get_or_create(
        id_usuario=user_id,
        email=email,
        nombre=(" ".join((nombre.split("+")))),
        password=generate_random_password(),
    )

    # Si el usuario fue creado, asignarle un rol y otros detalles
    if created:
        # Mapear el valor del campo "roles" del JSON a un rol en la base de datos
        if roles == "Instructor":
            rol = Rol.objects.get(nombre=Rol.PROFESOR)
        elif roles == "Learner":
            rol = Rol.objects.get(nombre=Rol.ESTUDIANTE)

        if rol:
            user.roles.add(rol)

        # Crear un perfil adicional para el usuario basado en su rol
        context_label = data.get("context_label")
        asignatura = context_label.split("_")[3]

        if rol.nombre == Rol.ESTUDIANTE:
            context_title = data.get("context_title")
            paralelo = context_title.split("Paralelos:")[1]
            semestre = context_label.split("_")[0]
            Estudiante.objects.create(
                usuario=user,
                asignatura=asignatura,
                paralelo=paralelo,
                semestre=semestre,
            )
        elif rol.nombre == Rol.PROFESOR:
            Docente.objects.create(usuario=user, asignatura=asignatura)

    return user
