from datetime import timedelta
import json
from django.forms import IntegerField
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from rest_framework.views import APIView
from exercise.swagger_serializers import (
    ExerciseSerializerCreateDocumentation,
    ExerciseSerializerCreateTeacherDocumentation,
)
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
from django.db.models import Count, Sum, Max, Q, Window, F, Count, Sum, F, Avg, Min, Max
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
import requests
from django.core.exceptions import ObjectDoesNotExist


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


class ExerciseDeleteView(APIView):
    def delete(self, request, exercise_id):
        try:
            exercise = Exercise.objects.get(exercise_id=exercise_id)
            exercise.delete()
        except Exercise.DoesNotExist:
            return Response(
                {"error": "Ejercicio no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {"message": "Ejercicio eliminado correctamente."}, status=status.HTTP_200_OK
        )


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

    @swagger_auto_schema(request_body=ExerciseSerializerCreateDocumentation)
    @transaction.atomic
    def post(self, request):
        try:
            user = request.user
            print("user: ", user.pk, flush=True)
            data = request.data.copy()
            data["user"] = user.pk
            print("data: ", data, flush=True)
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
        except Exception as e:
            print("error: ", e)
            return Response(
                {"error": "Ocurrió un error inesperado: " + str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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
            data["user"] = user.pk

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
    @transaction.atomic
    def put(self, request, exercise_id):
        try:
            user = request.user
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
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            Exercises = Exercise.objects.all()
            paginator = PageNumberPagination()
            paginated_Exercises = paginator.paginate_queryset(Exercises, request)
            serializer = ExerciseListSerializerAll(
                paginated_Exercises, many=True, context={"request": request}
            )

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


class ExerciseListSubjectView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request, subject):
        try:
            user = request.user
            subject = user.subject.get("subject", None) if user.subject else None

            if not subject:
                return Response(
                    {"error": "Subject no encontrado para el usuario."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            Exercises = Exercise.objects.filter(subject=subject)
            paginator = PageNumberPagination()
            paginated_Exercises = paginator.paginate_queryset(Exercises, request)
            serializer = ExerciseListSerializerAll(
                paginated_Exercises, many=True, context={"request": request}
            )

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

    @swagger_auto_schema(request_body=AttemptExerciseGPTSerializer)
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
        result = execute_code(
            code, exercise_instance.head, exercise_instance.tail, casos_de_uso
        )
        print("result: ", result, flush=True)
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
            True,
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
        user = CustomUser.objects.get(pk=user_id)

        attempts_exercises = AttemptExercise.objects.filter(user_id=user_id)
        data = []

        for attempt_exercise in attempts_exercises:
            exercise = attempt_exercise.exercise_id
            attempt_details = AttemptDetail.objects.filter(
                general_attempt_id=attempt_exercise
            ).order_by("date")

            attempt_data = {
                "exercise_id": exercise.exercise_id,
                "title": exercise.title,
                "difficulty": exercise.difficulty,
                "programming_language": exercise.programming_language,
                "subject": exercise.subject,
                "attempts_details": [],
                "max_score": attempt_details.aggregate(Max("score"))["score__max"],
                "min_score": attempt_details.aggregate(Min("score"))["score__min"],
                "avg_score": attempt_details.aggregate(Avg("score"))["score__avg"],
            }

            for detail in attempt_details:
                feedback_ids = FeedbackDetail.objects.filter(
                    attempt_id=detail
                ).values_list("feedback_id", flat=True)
                attempt_data["attempts_details"].append(
                    {
                        "attempt_id": detail.attempt_id,
                        "date": detail.date,
                        "score": detail.score,
                        "result": detail.result,
                        "feedback_ids": list(feedback_ids),
                    }
                )

            data.append(attempt_data)

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
                        "picture": user.picture.url if user.picture else None,
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
                            "picture": user.picture.url if user.picture else "",
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
            CustomUser.objects.get(pk=user_id)

            attempts = AttemptExercise.objects.filter(
                exercise_id=exercise_id, user_id=user_id
            )

            response_data = []

            for attempt in attempts:
                attempt_data = {
                    "general_attempt_id": attempt.general_attempt_id,
                    "score": attempt.score,
                    "result": attempt.result,
                    "details": [],
                }

                detail_attempts = AttemptDetail.objects.filter(
                    general_attempt_id=attempt
                )
                for detail in detail_attempts:
                    detail_data = {
                        "attempt_id": detail.attempt_id,
                        "date": detail.date,
                        "score": detail.score,
                        "result": detail.result,
                        "feedback": detail.feedback,
                    }

                    feedback_details = FeedbackDetail.objects.filter(attempt_id=detail)
                    feedback_info = []
                    for feedback in feedback_details:
                        code_content = None
                        results_content = None

                        if feedback.code_file:
                            code_content = (
                                default_storage.open(feedback.code_file.name)
                                .read()
                                .decode("utf-8")
                            )
                        if feedback.result_file:
                            results_content = json.loads(
                                default_storage.open(feedback.result_file.name)
                                .read()
                                .decode("utf-8")
                            )

                        feedback_info = {
                            "feedback_id": feedback.feedback_id,
                            "code": code_content,
                            "results": results_content,
                        }
                    detail_data["feedback_details"] = feedback_info

                    attempt_data["details"].append(detail_data)

                response_data.append(attempt_data)

            return Response(response_data, status=200)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=404)
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"}, status=500
            )


class FeedbackInfoView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, feedback_id):
        try:
            feedback = FeedbackDetail.objects.get(pk=feedback_id)
            serializer_data = FeedbackDetailSerializer(feedback).data
            if feedback.code_file:
                with feedback.code_file.open("r") as file:
                    serializer_data["code"] = file.read()
            if feedback.conversation_file:
                with feedback.conversation_file.open("r") as file:
                    serializer_data["conversation"] = json.load(file)
            if feedback.result_file:

                with feedback.result_file.open("r") as file:
                    serializer_data["results"] = file.read()
                    serializer_data["results"] = json.loads(serializer_data["results"])

            serializer_data.pop("conversation_file")
            serializer_data.pop("result_file")
            serializer_data.pop("code_file")
            return Response(serializer_data, status=200)
        except FeedbackDetail.DoesNotExist:
            return Response({"error": "FeedbackDetail not found."}, status=404)
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"}, status=500
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


class AttemptExerciseCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=AttemptExerciseSerializer)
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        user = request.user

        data = format_entry_data(request.data)
        code = data.get("code", "")
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
        result = execute_code(
            code, exercise_instance.head, exercise_instance.tail, casos_de_uso
        )
        print("result: ", result, flush=True)
        if "Error" in result:
            return Response({"error": result}, status=status.HTTP_400_BAD_REQUEST)

        outputs_esperados = [str(caso["output"]).strip() for caso in casos_de_uso]
        result_limpios = []
        for output in result:

            output_limpio = output.strip().rstrip("\n")
            result_limpios.append(output_limpio)

        print("Resultados limpios:", result_limpios, flush=True)
        score, resuelto = compare_outputs_and_calculate_score(
            outputs_esperados, result_limpios, exercise_instance.binary
        )
        results_json = generate_result_json(outputs_esperados, result_limpios)

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
            "No hay retroalimentación",
            code,
            data["exercise_id"],
            results_json,
            False,
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
            users = CustomUser.objects.filter(
                attemptexercise__exercise_id__in=exercises
            ).distinct()

            enriched_attempts = []
            for user in users:
                user_id = user.pk
                difficulty_success_rates = calculate_success_rate_for_difficulties(
                    user_id, exercises
                )
                content_success_rates = calculate_success_rate_for_contents(
                    user_id, exercises, subject
                )
                user_attempts = AttemptExercise.objects.filter(
                    user_id=user_id, exercise_id__in=exercises
                )

                total_score = (
                    AttemptExercise.objects.filter(
                        user_id=user_id, exercise_id__in=exercises
                    ).aggregate(Sum("score"))["score__sum"]
                    or 0
                )
                total_attempts = (
                    AttemptExercise.objects.filter(
                        user_id=user_id, exercise_id__in=exercises
                    ).aggregate(total=Sum("attempts"))["total"]
                    or 0
                )
                correct_attempts = AttemptDetail.objects.filter(
                    general_attempt_id__in=AttemptExercise.objects.filter(
                        user_id=user_id, exercise_id__in=exercises
                    ),
                    result=True,
                ).count()
                exercises_completed = AttemptExercise.objects.filter(
                    user_id=user_id, exercise_id__in=exercises, result=True
                ).count()
                success_rate = (
                    (correct_attempts / total_attempts * 100.0) if total_attempts else 0
                )
                average_score = (
                    AttemptDetail.objects.filter(
                        general_attempt_id__in=user_attempts
                    ).aggregate(Avg("score"))["score__avg"]
                    or 0
                )
                min_score = (
                    AttemptDetail.objects.filter(
                        general_attempt_id__in=user_attempts
                    ).aggregate(Min("score"))["score__min"]
                    or 0
                )
                max_score = (
                    AttemptDetail.objects.filter(
                        general_attempt_id__in=user_attempts
                    ).aggregate(Max("score"))["score__max"]
                    or 0
                )

                enriched_attempts.append(
                    {
                        "user_id": user_id,
                        "total_score": total_score,
                        "exercises_completed": exercises_completed,
                        "correct_attempts": correct_attempts,
                        "total_attempts": total_attempts,
                        "success_rate": success_rate,
                        "average_score": average_score,
                        "min_score": min_score,
                        "max_score": max_score,
                        "difficulty_success_rates": difficulty_success_rates,
                        "content_success_rates": content_success_rates,
                        "user_details": {
                            "name": user.name,
                            "email": user.email,
                            "picture": user.picture.url if user.picture else None,
                        },
                    }
                )

            return Response(enriched_attempts, status=status.HTTP_200_OK)
        except Subject.DoesNotExist:
            return Response(
                {"error": "Subject not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RankingPerSubjectSectionView(APIView):
    if settings.DEVELOPMENT_MODE:
        authentication_classes = []
        permission_classes = []
    else:
        authentication_classes = [JWTAuthentication]
        permission_classes = [IsAuthenticated]

    def get(self, request, subject, section):
        try:
            subject_instance = Subject.objects.get(name=subject)
            exercises = Exercise.objects.filter(subject=subject)

            students_in_section = CustomUser.objects.filter(
                subject__sections__contains=[section], subject__has_key="subject"
            ).values_list("user_id", flat=True)

            print(students_in_section, flush=True)
            attempts_queryset = AttemptExercise.objects.filter(
                exercise_id__in=exercises, user_id__in=students_in_section
            )

            enriched_attempts = []

            for user_id in students_in_section:
                user_attempts = attempts_queryset.filter(user_id=user_id)
                total_score = user_attempts.aggregate(Sum("score"))["score__sum"] or 0
                total_attempts = user_attempts.count()
                correct_attempts = AttemptDetail.objects.filter(
                    general_attempt_id__in=user_attempts, result=True
                ).count()
                exercises_completed = user_attempts.filter(result=True).count()
                success_rate = (
                    (correct_attempts / total_attempts * 100.0) if total_attempts else 0
                )

                average_score = (
                    AttemptDetail.objects.filter(
                        general_attempt_id__in=user_attempts
                    ).aggregate(Avg("score"))["score__avg"]
                    or 0
                )
                min_score = (
                    AttemptDetail.objects.filter(
                        general_attempt_id__in=user_attempts
                    ).aggregate(Min("score"))["score__min"]
                    or 0
                )
                max_score = (
                    AttemptDetail.objects.filter(
                        general_attempt_id__in=user_attempts
                    ).aggregate(Max("score"))["score__max"]
                    or 0
                )

                user = CustomUser.objects.get(pk=user_id)
                enriched_attempts.append(
                    {
                        "user_id": user_id,
                        "total_score": total_score,
                        "exercises_completed": exercises_completed,
                        "correct_attempts": correct_attempts,
                        "total_attempts": total_attempts,
                        "success_rate": success_rate,
                        "average_score": average_score,
                        "min_score": min_score,
                        "max_score": max_score,
                        "user_details": {
                            "name": user.name,
                            "email": user.email,
                            "picture": user.picture.url if user.picture else None,
                        },
                        "difficulty_success_rates": calculate_success_rate_for_difficulties(
                            user_id, exercises
                        ),
                        "content_success_rates": calculate_success_rate_for_contents(
                            user_id, exercises, subject
                        ),
                    }
                )

            return Response(enriched_attempts, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response(
                {"error": "Subject or Section not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ExerciseGeneratorView(APIView):
    # authentication_classes = [JWTAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        response = requests.post(
            url="http://localhost:3002",
            data=json.dumps({"query": "conditionals, loops, medium easy"}),
            headers={"Content-Type": "application/json"},
        )
        return Response({"message": response}, status=status.HTTP_200_OK)


class CodeExecutionView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(request_body=CodeExecutionSerializer)
    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = CodeExecutionSerializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data["code"]
            exercise_instance = serializer.validated_data["exercise_id"]

            if verify_imports(code):
                return Response(
                    {"error": "Librerías importadas detectadas"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            casos_de_uso = load_use_case(exercise_instance.id)
            result = execute_code(
                code, exercise_instance.head, exercise_instance.tail, casos_de_uso
            )

            if "Error" in result:
                return Response({"error": result}, status=status.HTTP_400_BAD_REQUEST)

            outputs_esperados = [str(caso["output"]).strip() for caso in casos_de_uso]
            result_limpio = [linea.strip() for linea in result.splitlines()]
            results_json = generate_result_json(outputs_esperados, result_limpio)

            return Response(
                {
                    "message": "Código ejecutado con éxito",
                    "result": results_json,
                },
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
