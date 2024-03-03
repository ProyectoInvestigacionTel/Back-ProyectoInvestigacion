from django.urls import include, path
from .views import *

urlpatterns = [
    path("<int:pk>", ExerciseView.as_view()),
    path("create", ExerciseCreateView.as_view(), name="Exercise-create"),
    path(
        "list",
        ExerciseListView.as_view(),
    ),
    path(
        "list/<str:subject>",
        ExerciseListSubjectView.as_view(),
        name="Exercise-list-subject",
    ),
    path(
        "detail/<int:exercise_id>",
        ExerciseDeleteView.as_view(),
        name="exercise-detelete",
    ),
    path(
        "attempt_gpt", AttemptExerciseCreateGPTView.as_view(), name="Register-attempt"
    ),
    path("attempt", AttemptExerciseCreateView.as_view(), name="Attempt-list"),
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
        "ranking-subject/<str:subject>/",
        RankingPerSubjectView.as_view(),
        name="ranking-subject",
    ),
    path(
        "generator",
        ExerciseGeneratorView.as_view(),
        name="exercise-generator",
    ),
    path("use_cases/", include("exercise.use_case.urls")),
]
