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


class UseCaseUploadView(APIView):
    parser_classes = [FileUploadParser]

    def post(self, request, exercise_id, format=None):
        try:
            if "file" not in request.data:
                return Response(
                    {"error": "Archivo no subido"}, status=status.HTTP_400_BAD_REQUEST
                )

            exercise = Exercise.objects.filter(id=exercise_id).first()
            if not exercise:
                return Response(
                    {"error": "Ejercicio no encontado"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            file_obj = request.data["file"]

            with zipfile.ZipFile(file_obj, "r") as zip_ref:
                temp_dir = "/tmp/use_cases/"
                zip_ref.extractall(temp_dir)

                for input_file_name in os.listdir(temp_dir + "input"):
                    base_name = os.path.splitext(input_file_name)[0]
                    output_file_name = f"{base_name}.txt"

                    with open(
                        os.path.join(temp_dir, "input", input_file_name), "r"
                    ) as input_file, open(
                        os.path.join(temp_dir, "output", output_file_name), "r"
                    ) as output_file:
                        input_code = input_file.read()
                        output_code = output_file.read()
                        UseCase.objects.create(
                            exercise=exercise,
                            input_code=input_code,
                            output_code=output_code,
                        )

            os.remove(temp_dir)

            return Response(
                {
                    "message": "Casos de uso cargados correctamente",
                    "use_cases": UseCaseSerializer(
                        UseCase.objects.filter(exercise=exercise), many=True
                    ).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
