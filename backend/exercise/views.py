from datetime import timedelta
import json
from django.forms import IntegerField
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from exercise.swagger_serializers import ExerciseSerializerCreateTeacherDocumentation
from user.models import *
from user.models import CustomUser
from .models import *
from .serializers import *
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from drf_yasg import openapi

from django.conf import settings
from .aux_func_views import *
from django.db.models.functions import Rank
from django.db.models import (
    Count,
    Sum,
    Max,
    Q,
    Window,
    F,
    Count,
    Sum,
    F,
    FloatField,
    ExpressionWrapper,
    Avg,
    Case,
    When,
    IntegerField,
)
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
import requests

class ExerciseView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]
    queryset = Exercise.objects.all()
    serializer_class = ExerciseSerializerView

    def get(self, request, pk):
        try:
            exercise = Exercise.objects.get(pk=pk)
        except Exercise.DoesNotExist:
            return Response(
                {"error": "Ejercicio no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = ExerciseSerializerView(exercise)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SearchExercisesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "contents",
                openapi.IN_QUERY,
                description="Una lista de contents separados por comas",
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                "difficulty",
                openapi.IN_QUERY,
                description="Nivel de difficulty",
                type=openapi.TYPE_STRING,
            ),
        ]
    )
    def get(self, request):
        request.query_params = format_entry_data(request.query_params)
        contents = request.query_params.get("contents", None)
        difficulty = request.query_params.get("difficulty", None)

        if not contents and not difficulty:
            return Response(
                {
                    "error": "Por favor, proporciona contents y/o difficulty para buscar."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        query_filters = Q()

        if contents:
            contents_list = contents.split(",")
            queries = [Q(contents__icontains=content) for content in contents_list]
            query_filters |= queries.pop()  # Usa el operador |= para combinar con OR
            for query in queries:
                query_filters |= query

        if difficulty:
            query_filters &= Q(
                difficulty=difficulty
            )  # Usa el operador &= para combinar con AND

        Exercises = Exercise.objects.filter(query_filters)

        response_data = []
        for Exercise in Exercises:
            serializer = ExerciseSerializerView(Exercise)

            Exercise_data = serializer.data
            Exercise_data = get_all_exercises_files(Exercise.exercise_id, Exercise_data)
            Exercise_data = serializer.data
            Exercise_data["title"] = Exercise.title
            Exercise_data["constraints"] = Exercise.constraints
            response_data.append(Exercise_data)

        return Response(response_data, status=status.HTTP_200_OK)


class ExerciseCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=ExerciseSerializerCreate)
    def post(self, request):
        user = request.user

        data = request.data.copy()
        data["user"] = user.pk
        serializer = ExerciseSerializerCreate(data=data)

        if serializer.is_valid():
            exercise = serializer.save()
            return Response(
                {
                    "message": "Ejercicio creado correctamente",
                    "exercise_id": exercise.pk,
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExerciseCreateViewTeacher(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=ExerciseSerializerCreateTeacherDocumentation)
    def post(self, request):
        try:
            user = request.user
            if settings.DEVELOPMENT_MODE:
                user = CustomUser.objects.get(user_id="02")
            data = request.data.copy()
            data["user"] = user.user_id

            serializer = ExerciseSerializerCreateTeacher(data=data)

            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "Ejercicio creado correctamente"},
                    status=status.HTTP_201_CREATED,
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "Ocurrió un error inesperado: " + str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExerciseUpdateViewTeacher(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=ExerciseSerializerUpdateTeacher)
    def put(self, request, exercise_id):
        try:
            user = request.user
            if settings.DEVELOPMENT_MODE:
                user = CustomUser.objects.get(user_id="02")
            print("user: ", user)
            data = request.data.copy()

            try:
                exercise_instance = Exercise.objects.get(exercise_id=exercise_id)
            except Exercise.DoesNotExist:
                return Response(
                    {"error": "Ejercicio no encontrado"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            serializer = ExerciseSerializerUpdateTeacher(exercise_instance, data=data)

            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"message": "Ejercicio actualizado correctamente"},
                    status=status.HTTP_200_OK,
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": "Ocurrio un error inesperado: " + str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExerciseListView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            Exercises = Exercise.objects.all()
            paginator = PageNumberPagination()
            paginated_Exercises = paginator.paginate_queryset(Exercises, request)
            serializer = ExerciseListSerializerAll(paginated_Exercises, many=True)

            return paginator.get_paginated_response(serializer.data)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print("error: ", e)
            return Response(
                {"error": "Ocurrió un error inesperado"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AttemptExerciseCreateGPTView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=AttemptExerciseSerializer)
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user

        data = format_entry_data(request.data)
        code = data.get("code", "")
        initial_feedback = data.get("initial_feedback", "")
        user = CustomUser.objects.get(pk=user.user_id)

        if verify_imports(code):
            return Response(
                {"error": "Librerías importadas detectadas"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exercise_instance = get_excercise_instance(data["exercise_id"])
        if exercise_instance is None:
            return Response(
                {"error": "Exercise no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )
        print("Exercise_instance: ", exercise_instance.__dict__)
        attempt_existente = get_current_attempt(request, user)

        casos_de_uso = load_use_case(exercise_instance.exercise_id)
        print("use_cases: ", casos_de_uso)
        result = execute_code(code, exercise_instance.head, exercise_instance.tail)
        print("result: ", result)
        if "Error" in result:
            return Response({"error": result}, status=status.HTTP_400_BAD_REQUEST)

        outputs_esperados = [str(caso["output"]).strip() for caso in casos_de_uso]

        result_limpio = [linea.strip() for linea in result.splitlines()]
        score, resuelto = compare_outputs_and_calculate_score(
            outputs_esperados, result_limpio, exercise_instance.binary
        )
        results_json = generate_result_json(outputs_esperados, result_limpio)

        attempt_instance = update_attempt(
            attempt_existente, request, exercise_instance, user, score, resuelto
        )
        if not attempt_instance:
            return Response(
                {"error": "Error al actualizar o crear el attempt"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        detail_instance = create_or_update_attempt_detal(
            attempt_instance, score, resuelto
        )
        if detail_instance is None:
            return Response(
                {"error": "Error al crear o actualizar el detail del attempt"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        retro_instance = create_or_update_feedback(
            detail_instance,
            initial_feedback,
            code,
            data["exercise_id"],
            results_json,
        )
        if retro_instance is None:
            return Response(
                {"error": "Error al crear o actualizar la retroalimentación"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        update_result_state_and_score(detail_instance, user, score)

        return Response(
            {
                "message": "attempt registrado con éxito",
                "feedback_id": retro_instance.feedback_id,
                "result": resuelto,
            },
            status=status.HTTP_201_CREATED,
        )


class InfoExercisesPerUserView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        data = []

        try:
            CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )
        exercises = Exercise.objects.filter(user_id=user_id)

        for exercise in exercises:
            max_score = AttemptDetail.objects.filter(
                general_attempt_id__exercise_id=exercise
            ).aggregate(Max("score"))["score__max"]
            exercise_data = {
                "exercise_id": exercise.exercise_id,
                "title": exercise.title,
                "creation_date": exercise.date,
                "difficulty": exercise.difficulty,
                "contents": exercise.contents,
                "programming_language": exercise.programming_language,
                "subject": exercise.subject,
                "max_score": exercise.score,
                "obtained_score": max_score if max_score else "No resuelto",
                "attempts": {},
            }

            general_attempts = AttemptExercise.objects.filter(
                user_id=user_id, exercise_id=exercise.exercise_id
            ).distinct("exercise_id")
            for general_attempt in general_attempts:
                attempt_detail = AttemptDetail.objects.filter(
                    general_attempt_id=general_attempt
                )

                for index, attempt_detail in enumerate(attempt_detail, start=1):
                    # Obtener details de retroalimentación
                    feedback_detail = FeedbackDetail.objects.filter(
                        attempt_id=attempt_detail
                    ).first()

                    # Leer el código y la conversación desde los archivos si están presentes
                    if feedback_detail:
                        if feedback_detail.code_file and feedback_detail.code_file:
                            with feedback_detail.code_file.open("r") as file:
                                code = file.read()
                            with feedback_detail.conversation_file.open("r") as file:
                                conversation = json.load(file)

                    exercise_data["attempts"][f"attempt_{index}"] = {
                        "score": attempt_detail.score,
                        "date": attempt_detail.date.strftime("%Y-%m-%d %H:%M:%S"),
                        "code": code,
                        "conversation": conversation,
                    }

            data.append(format_response_data(exercise_data))

        return Response(data, status=status.HTTP_200_OK)


class RankingExerciseView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request, exercise_id):
        try:
            attempts = AttemptExercise.objects.filter(exercise_id=exercise_id).order_by(
                "-score"
            )

            ranking = []

            for attempt in attempts:
                user = get_user_model().objects.get(pk=attempt.user_id.pk)

                total_attempts = AttemptDetail.objects.filter(
                    general_attempt_id=attempt.general_attempt_id
                ).count()

                correct_attempts = AttemptDetail.objects.filter(
                    general_attempt_id=attempt.general_attempt_id, result=True
                ).count()

                success_rate = (
                    (correct_attempts / total_attempts * 100) if total_attempts else 0
                )

                ranking.append(
                    {
                        "user_id": user.pk,
                        "name": user.name,
                        "email": user.email,
                        "total_attempts": total_attempts,
                        "correct_attempts": correct_attempts,
                        "success_rate": success_rate,
                        "score": attempt.score,
                    }
                )

            # Return the response with the ranking list
            return Response(ranking, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except AttemptExercise.DoesNotExist:
            return Response(
                {"error": "Attempt for Exercise not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": "An unexpected error occurred: " + str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExercisesPerSubjectView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request, subject):
        try:
            exercises = Exercise.objects.filter(subject=subject)

            exercises_list = []
            for exercise in exercises:
                user = CustomUser.objects.get(pk=exercise.user_id)
                exercises_list.append(
                    format_response_data(
                        {
                            "exercise_id": exercise.exercise_id,
                            "max_score": (
                                AttemptExercise.objects.filter(
                                    exercise_id=exercise.exercise_id
                                )
                                .order_by("-score")
                                .first()
                                .score
                                if AttemptExercise.objects.filter(
                                    exercise_id=exercise.exercise_id
                                ).exists()
                                else 0
                            ),
                            "difficulty": exercise.difficulty,
                            "contents": exercise.contents,
                            "user_id": user.user_id,
                            "email": user.email,
                            "name": user.name,
                        }
                    )
                )

            return Response(exercises_list, status=status.HTTP_200_OK)

        except Exercise.DoesNotExist:
            return Response(
                {"error": "Ejercicios no encontrados"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print("error: ", e)
            return Response(
                {"error": "Ocurrió un error inesperado"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ConversationView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=conversationSerializer)
    def post(self, request, feedback_id):
        try:
            detail = FeedbackDetail.objects.get(pk=feedback_id)
        except FeedbackDetail.DoesNotExist:
            return Response(
                {"error": "FeedbackDetail no encontrado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = conversationSerializer(data=request.data)
        if serializer.is_valid():
            for mensaje_data in serializer.validated_data["mensajes"]:
                remitente = mensaje_data["remitente"]
                mensaje = mensaje_data["mensaje"]
                add_message_to_conversation(detail, remitente, mensaje)

            return Response(
                {"message": "Mensajes añadidos con éxito."},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DetailPerExercise(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request, exercise_id, user_id):
        try:
            user = CustomUser.objects.get(pk=user_id)
            attempts = AttemptExercise.objects.filter(
                exercise_id=exercise_id, user_id=user_id
            )

            for attempt in attempts:
                detail_attempts = AttemptDetail.objects.filter(
                    general_attempt_id=attempt.general_attempt_id
                )

                lista = []
                for retro in detail_attempts:
                    feedback_details = FeedbackDetail.objects.filter(
                        attempt_id=retro.attempt_id
                    )
                    if feedback_details.exists():
                        feedback_detail = feedback_details[0]
                        results_content = None

                        if (
                            hasattr(feedback_detail, "result_file")
                            and feedback_detail.result_file
                        ):
                            with default_storage.open(
                                feedback_detail.result_file.path, "r"
                            ) as file:
                                results_content = json.load(file)
                        lista.append(
                            format_response_data(
                                {
                                    "feedback_id": feedback_detail.feedback_id,
                                    "results": results_content,
                                }
                            )
                        )

            return Response(lista, status=status.HTTP_200_OK)
        except CustomUser.DoesNotExist:
            return Response(
                {"error": "user no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )
        except AttemptExercise.DoesNotExist:
            return Response(
                {"error": "attempt de Exercise no encontrado"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": "Ocurrió un error inesperado"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SubjectInfoView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request, subject):
        try:
            exercises_per_subject = Exercise.objects.filter(subject=subject)

            # Agregar información por contents
            exercises_per_contents = exercises_per_subject.values("contents").annotate(
                qty=Count("exercise_id")
            )
            # Total de Exercises en la subject
            total_exercises = exercises_per_subject.count()

            # Agregar información por difficulty
            difficultyes = exercises_per_subject.values("difficulty").annotate(
                qty=Count("exercise_id")
            )

            # Calcular percentages por difficulty
            percentages_per_difficulty = {}
            for difficulty in difficultyes:
                percentage = (
                    (difficulty["qty"] / total_exercises) * 100
                    if total_exercises > 0
                    else 0
                )
                percentages_per_difficulty[difficulty["difficulty"]] = percentage

            data = {
                "exercises_per_contents": list(exercises_per_contents),
                "generated_exercises": exercises_per_subject.count(),
                "made_execises": 0,
                "made_percentage": 0,
                "percentages_per_difficulty": percentages_per_difficulty,
            }

            # Calcular Exercises realizados
            for exercises_of_subject in exercises_per_subject:
                attempts_per_subject = AttemptExercise.objects.filter(
                    exercise_id=exercises_of_subject.exercise_id
                )
                data["made_execises"] += attempts_per_subject.count()

            # Calcular el percentage de Exercises realizados
            if data["generated_exercises"] > 0:
                data["made_percentage"] = (
                    data["made_execises"] / data["generated_exercises"]
                ) * 100

            # Calcular la suma de scores por Student y crear un ranking
            ranking = (
                AttemptExercise.objects.filter(exercise_id__subject=subject)
                .values("user_id")
                .annotate(total_score=Sum("exercise_id__score"))
                .annotate(
                    ranking=Window(expression=Rank(), order_by=F("total_score").desc())
                )
            )
            user = CustomUser.objects.get(user_id=ranking[0]["user_id"])
            data["user_id"] = user.user_id
            data["email"] = user.email
            data["name"] = user.name
            data["total_score"] = ranking[0]["total_score"]
            data["ranking"] = ranking[0]["ranking"]

            return Response(format_response_data(data), status=status.HTTP_200_OK)
        except Exercise.DoesNotExist:
            return Response(
                {"error": "subject no encontrada"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:

            return Response(
                {"error": "Ocurrió un error inesperado: " + str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LastExerciseView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request, user_id):
        try:
            last_exercise = (
                Exercise.objects.filter(user_id=user_id).order_by("-date").first()
            )

            if last_exercise:
                current_time = timezone.now()
                time_diff = current_time - last_exercise.date

                result = time_diff > timedelta(days=1)
            else:
                result = True

            return Response({"message": result}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": "Ocurrió un error inesperado: " + str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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


class AttemptExerciseCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=AttemptExerciseSerializer)
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user

        data = format_entry_data(request.data)
        code = data.get("code", "")
        initial_feedback = data.get("initial_feedback", "")
        user = CustomUser.objects.get(pk=user.user_id)

        if verify_imports(code):
            return Response(
                {"error": "Librerías importadas detectadas"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exercise_instance = get_excercise_instance(data["exercise_id"])
        if exercise_instance is None:
            return Response(
                {"error": "Exercise no encontrado"}, status=status.HTTP_404_NOT_FOUND
            )
        print("Exercise_instance: ", exercise_instance.__dict__)
        attempt_existente = get_current_attempt(request, user)

        casos_de_uso = load_use_case(exercise_instance.exercise_id)
        print("use_cases: ", casos_de_uso)
        result = execute_code(code, exercise_instance.head, exercise_instance.tail)
        print("result: ", result)
        if "Error" in result:
            return Response({"error": result}, status=status.HTTP_400_BAD_REQUEST)

        outputs_esperados = [str(caso["output"]).strip() for caso in casos_de_uso]

        result_limpio = [linea.strip() for linea in result.splitlines()]
        score, resuelto = compare_outputs_and_calculate_score(
            outputs_esperados, result_limpio, exercise_instance.binary
        )
        results_json = generate_result_json(outputs_esperados, result_limpio)

        attempt_instance = update_attempt(
            attempt_existente, request, exercise_instance, user, score, resuelto
        )
        if not attempt_instance:
            return Response(
                {"error": "Error al actualizar o crear el attempt"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        detail_instance = create_or_update_attempt_detal(
            attempt_instance, score, resuelto
        )
        if detail_instance is None:
            return Response(
                {"error": "Error al crear o actualizar el detail del attempt"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "message": "attempt registrado con éxito",
                "result": resuelto,
                "detail_use_cases": results_json,
            },
            status=status.HTTP_201_CREATED,
        )


class RankingPerSubjectView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request, subject):
        try:
            exercises = Exercise.objects.filter(subject=subject)
            attempts = (
                AttemptExercise.objects.filter(exercise_id__in=exercises)
                .values("user_id")
                .annotate(
                    total_score=Sum("score"),
                    exercises_completed=Count("exercise_id", distinct=True),
                    correct_attempts=Sum(
                        Case(
                            When(result=True, then=1),
                            default=0,
                            output_field=IntegerField(),
                        )
                    ),
                    total_attempts=Count("exercise_id"),
                )
                .annotate(
                    success_rate=ExpressionWrapper(
                        F("correct_attempts") * 100.0 / F("total_attempts"),
                        output_field=FloatField(),
                    )
                )
                .order_by("-total_score", "-exercises_completed", "-success_rate")
            )

            enriched_attempts = [
                {
                    **attempt,
                    "user_details": CustomUser.objects.filter(pk=attempt["user_id"])
                    .values("name", "email")
                    .first(),
                }
                for attempt in attempts
            ]

            return Response(enriched_attempts, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ExerciseGeneratorView(APIView):
    #authentication_classes = [JWTAuthentication]
    #permission_classes = [IsAuthenticated]

    def get(self, request):
        response = requests.post(
            url='http://localhost:3002',
            data=json.dumps({"query":"conditionals, loops, medium easy"}),
            headers={"Content-Type": "application/json"}
        )
        return Response({"message": response}, status=status.HTTP_200_OK)