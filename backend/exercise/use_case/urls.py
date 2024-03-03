from django.urls import path
from .views import *


urlpatterns = [
    path(
        "<int:exercise_id>/",
        UseCasesListView.as_view(),
        name="use-cases-list",
    ),
    path(
        "<int:exercise_id>/<int:use_case_id>/",
        UseCasesDeleteView.as_view(),
        name="use-case-delete",
    ),
    path(
        "<int:exercise_id>",
        UseCasesCreateView.as_view(),
        name="use-case-bulk-create",
    ),
    path(
        "upload_zip/<int:exercise_id>", UseCaseUploadView.as_view(), name="upload-file"
    ),
]
