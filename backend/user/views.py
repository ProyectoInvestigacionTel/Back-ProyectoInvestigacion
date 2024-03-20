from teloprogramo.settings import SECRET_KEY
from .aux_func_views import (
    authenticate_or_create_user,
)
from drf_yasg import openapi
from .models import CustomUser, Teacher, Student, Rol
from .serializers import (
    CustomTokenObtainSerializer,
    CustomUserPhotoSerializer,
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
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from django.db import transaction
from django.shortcuts import redirect
import jwt
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


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


class UserEmailView(APIView):
    def get(self, request, email, *args, **kwargs):
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if (
            user.roles.filter(name="Teacher").exists()
            or user.roles.filter(name="TeacherAssistant").exists()
            or user.roles.filter(name="Coordinator").exists()
        ):
            teacher_instance = Teacher.objects.get(user=user.user_id)
            serializer = TeacherGETSerializer(teacher_instance)
        elif user.roles.filter(name="Student").exists():
            student_instance = Student.objects.get(user=user.user_id)
            serializer = StudentGETSerializer(student_instance)
        elif user.roles.filter(name="ADMIN").exists():
            serializer = CustomUserGETSerializer(user)
        else:
            return Response(
                {"error": "Rol de usuario no válido"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserIdView(APIView):
    def get(self, request, user_id):
        try:
            user = CustomUser.objects.get(user_id=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if (
            user.roles.filter(name="Teacher").exists()
            or user.roles.filter(name="TeacherAssistant").exists()
            or user.roles.filter(name="Coordinator").exists()
        ):
            teacher_instance = Teacher.objects.get(user=user.user_id)
            serializer = TeacherGETSerializer(teacher_instance)
        elif user.roles.filter(name="Student").exists():
            student_instance = Student.objects.get(user=user.user_id)
            serializer = StudentGETSerializer(student_instance)
        elif user.roles.filter(name="ADMIN").exists():
            serializer = CustomUserGETSerializer(user)
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
            # Si no se proporcionaron email y password, usar la función para autenticar o crear el usuario
            user = CustomUser.objects.filter(email=email).exists()

            if not user:
                user = authenticate_or_create_user(request.data)
            else:
                user = CustomUser.objects.get(email=email)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        access_token_payload = jwt.decode(
            access_token, SECRET_KEY, algorithms=["HS256"]
        )

        user_serializer = CustomUser.objects.get(email=user.email)
        user_data = {
            "user_id": user_serializer.user_id,
            "email": user_serializer.email,
            "name": user_serializer.name,
            "roles": [role.name for role in user_serializer.roles.all()],
            "institution": (
                user_serializer.institution.name if user_serializer.institution else ""
            ),
            "campus": user_serializer.campus if user_serializer.campus else "",
            "picture": user_serializer.picture.url if user_serializer.picture else "",
            "subject": user_serializer.subject,
        }

        if user_serializer.roles.filter(name="Student").exists():
            student = Student.objects.get(user=user_serializer)
            user_data["semester"] = student.semester

        access_token_payload["user_data"] = user_data
        access_token = jwt.encode(access_token_payload, SECRET_KEY, algorithm="HS256")

        # Redirige al usuario con los tokens y user_data incluidos en el accessToken
        redirect_url = f"https://teloprogramo.cl/auth?accessToken={access_token}&refreshToken={refresh_token}"
        return redirect(redirect_url)
    
    
class LoginUserLocal(APIView):
    parser_classes = [FormParser, JSONParser]

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
            # Si no se proporcionaron email y password, usar la función para autenticar o crear el usuario
            user = CustomUser.objects.filter(email=email).exists()

            if not user:
                user = authenticate_or_create_user(request.data)
            else:
                user = CustomUser.objects.get(email=email)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        access_token_payload = jwt.decode(
            access_token, SECRET_KEY, algorithms=["HS256"]
        )

        user_serializer = CustomUser.objects.get(email=user.email)
        user_data = {
            "user_id": user_serializer.user_id,
            "email": user_serializer.email,
            "name": user_serializer.name,
            "roles": [role.name for role in user_serializer.roles.all()],
            "institution": (
                user_serializer.institution.name if user_serializer.institution else ""
            ),
            "campus": user_serializer.campus if user_serializer.campus else "",
            "picture": user_serializer.picture.url if user_serializer.picture else "",
            "subject": user_serializer.subject,
        }

        if user_serializer.roles.filter(name="Student").exists():
            student = Student.objects.get(user=user_serializer)
            user_data["semester"] = student.semester

        access_token_payload["user_data"] = user_data
        access_token = jwt.encode(access_token_payload, SECRET_KEY, algorithm="HS256")

        # Redirige al usuario con los tokens y user_data incluidos en el accessToken
        redirect_url = f"http://localhost:3000/auth?accessToken={access_token}&refreshToken={refresh_token}"
        return redirect(redirect_url)

 
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

        user_data = {
            "user_id": user_serializer.user_id,
            "email": user_serializer.email,
            "name": user_serializer.name,
            "roles": [rol.name for rol in user_serializer.roles.all()],
            "institution": user_serializer.institution.name,
            "campus": user_serializer.campus,
            "subject": user_serializer.subject,
        }
        if Student.objects.filter(user=user_serializer).exists():
            student = Student.objects.get(user=user_serializer)
            user_data["semester"] = student.semester
        elif Teacher.objects.filter(user=user_serializer).exists():
            teacher = Teacher.objects.get(user=user_serializer)
        response_data = {**user_data, **token_data}
        return Response(response_data, status=status.HTTP_200_OK)


class GetCoinView(APIView):
    def get(self, request, user_id):
        try:
            user = CustomUser.objects.get(user_id=user_id)
            return Response({"coins": user.coins}, status=status.HTTP_200_OK)
        except:
            return Response(
                {"error": "No se pudo obtener las monedas"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class AddCoinView(APIView):
    def patch(self, request, user_id):
        try:
            coins = request.data.get("coins")
            user = CustomUser.objects.get(user_id=user_id)
            user.coins += coins
            user.save()
            return Response(
                {"user_id": user_id, "coins": user.coins}, status=status.HTTP_200_OK
            )
        except:
            return Response(
                {"error": "No se pudo agregar las monedas"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RemoveCoinView(APIView):
    def patch(self, request, user_id):
        try:
            coins = request.data.get("coins")
            user = CustomUser.objects.get(user_id=user_id)
            user.coins -= coins
            if user.coins < 0:
                user.coins = 0
            user.save()
            return Response(
                {"user_id": user_id, "coins": user.coins}, status=status.HTTP_200_OK
            )
        except:
            return Response(
                {"error": "No se pudo restar las monedas"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class UserPhotoUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                name="picture",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                description="Foto de perfil del usuario",
                required=True,
            ),
        ],
        responses={200: openapi.Response("Foto subida correctamente")},
    )
    def post(self, request, *args, **kwargs):
        user = request.user
        serializer = CustomUserPhotoSerializer(user, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserPhotoView(APIView):
    def get(self, request, user_id):
        try:
            user = CustomUser.objects.get(user_id=user_id)
            return Response({"picture": user.picture.url}, status=status.HTTP_200_OK)
        except:
            return Response(
                {"error": "No se pudo obtener la foto"},
                status=status.HTTP_400_BAD_REQUEST,
            )

