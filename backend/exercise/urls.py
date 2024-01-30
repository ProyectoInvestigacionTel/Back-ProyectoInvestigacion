from django.urls import path
from .views import *

urlpatterns = [
    path("<int:pk>", ExerciseView.as_view()),
    path("create", ExerciseCreateView.as_view(), name="Exercise-create"),
    path(
        "list",
        ExerciseListView.as_view(),
    ),
    path("attempt", AttemptExerciseCreateView.as_view(), name="Register-attempt"),
    path(
        "exercises-per-user/<str:user_id>",
        InfoExercisesPerUserView.as_view(),
        name="Exercises-per-user",
    ),
    path(
        "search_exercises",
        SearchExercisesView.as_view(),
        name="Search-exercises",
    ),
    path(
        "ranking/<int:exercise_id>",
        RankingExerciseView.as_view(),
        name="Eanking-Exercise",
    ),
    path(
        "exercises-per-subject/<str:subject>",
        ExercisesPerSubjectView.as_view(),
        name="Exercises-per-subject",
    ),
    path(
        "conversation/<int:feedback_id>",
        ConversationView.as_view(),
        name="Conversation",
    ),
    path(
        "detail-per-exercise/<int:exercise_id>/<str:user_id>",
        DetailPerExercise.as_view(),
        name="Detail-per-Exercise",
    ),
    path("subject-info/<str:subject>", SubjectInfoView.as_view(), name="subject-info"),
    path(
        "create_exercise/<str:user_id>",
        LastExerciseView.as_view(),
        name="Last-exercise",
    ),
    path(
        "create_exercise_teacher",
        ExerciseCreateViewTeacher.as_view(),
        name="Create-exercise-teacher",
    ),
    path(
        "update/<int:exercise_id>/",
        ExerciseUpdateViewTeacher.as_view(),
        name="Exercise-update",
    ),
    path(
        "use_cases/<int:exercise_id>/",
        UseCasesListView.as_view(),
        name="use-cases-list",
    ),
    path(
        "use_cases/<int:exercise_id>/<int:use_case_id>/",
        UseCasesDeleteView.as_view(),
        name="use-case-delete",
    ),
    path(
        "use_cases/<int:exercise_id>",
        UseCasesCreateView.as_view(),
        name="use-case-bulk-create",
    ),
]
