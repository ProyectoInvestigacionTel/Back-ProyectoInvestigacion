import os
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from user.models import *
from exercise.models import *
from exercise.use_case.serializers import *
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.conf import settings
import zipfile
from rest_framework.parsers import FileUploadParser
from drf_yasg import openapi
from rest_framework.parsers import MultiPartParser


class UseCasesDeleteView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def delete(self, request, exercise_id, use_case_id):
        try:
            UseCase.objects.get(id=use_case_id, exercise_id=exercise_id).delete()
            return Response(
                {
                    "message": f"Caso de uso numero {use_case_id} para ejercico {exercise_id} borrado correctamente"
                },
                status=status.HTTP_202_ACCEPTED,
            )
        except Exercise.DoesNotExist:
            return Response(
                {"error": "Caso de uso no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UseCasesListView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request, exercise_id):
        try:
            use_cases = UseCase.objects.filter(exercise_id=exercise_id)
            serializer = UseCaseSerializer(use_cases, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UseCase.DoesNotExist:
            return Response(
                {"error": "Caso de uso no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UseCasesCreateView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=UseCaseBulkCreateSerializer)
    def post(self, request, exercise_id):
        try:
            exercise = Exercise.objects.get(pk=exercise_id)
        except Exercise.DoesNotExist:
            return Response(
                {"error": "Ejercicio no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )

        use_cases_data = request.data.get("use_cases")
        if not isinstance(use_cases_data, list):
            return Response(
                {"error": "Formato invalido."}, status=status.HTTP_400_BAD_REQUEST
            )

        use_case_serializers = [UseCaseSerializer(data=data) for data in use_cases_data]

        with transaction.atomic():
            created_use_cases = []
            for serializer in use_case_serializers:
                if serializer.is_valid(raise_exception=True):
                    use_case = serializer.save(exercise_id=exercise.exercise_id)
                    created_use_cases.append(use_case)

        created_data = UseCaseSerializer(created_use_cases, many=True).data
        return Response(created_data, status=status.HTTP_201_CREATED)


class UseCasePutView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=UseCaseSerializer)
    def put(self, request, exercise_id, use_case_id):
        try:
            use_case = UseCase.objects.get(id=use_case_id, exercise_id=exercise_id)
            serializer = UseCaseSerializer(use_case, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UseCase.DoesNotExist:
            return Response(
                {"error": "Caso de uso no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class UseCaseUploadView(APIView):
    parser_classes = [MultiPartParser]
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "file",
                in_=openapi.IN_FORM,
                description="Archivo zip de casos de uso",
                type=openapi.TYPE_FILE,
                required=True,
            ),
        ],
        responses={201: UseCaseSerializer(many=True)},
    )
    def post(self, request, exercise_id, format=None):
        temp_dir = os.path.join(os.sep, "tmp", "use_cases")
        input_dir = os.path.join(temp_dir, "input")
        output_dir = os.path.join(temp_dir, "output")

        for directory in [temp_dir, input_dir, output_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)

        try:
            file_obj = request.FILES["file"]
            with zipfile.ZipFile(file_obj, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
                for input_file_name in os.listdir(input_dir):
                    base_name = os.path.splitext(input_file_name)[0]
                    output_file_name = f"{base_name.replace('input', 'output')}.txt"
                    output_file_path = os.path.join(output_dir, output_file_name)

                    if os.path.exists(output_file_path):
                        with open(
                            os.path.join(input_dir, input_file_name), "r"
                        ) as input_file, open(output_file_path, "r") as output_file:
                            input_code = input_file.read()
                            output_code = output_file.read()
                            UseCase.objects.create(
                                exercise_id=exercise_id,
                                input_code=input_code,
                                output_code=output_code,
                            )
                    else:
                        raise FileNotFoundError(
                            f"Output file not found: {output_file_path}"
                        )

            use_cases = UseCase.objects.filter(exercise_id=exercise_id)
            serializer = UseCaseSerializer(use_cases, many=True)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exercise.DoesNotExist:
            return Response(
                {"error": "Ejercicio no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )
        except FileNotFoundError as fnf_error:
            return Response(
                {"error": str(fnf_error)}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
