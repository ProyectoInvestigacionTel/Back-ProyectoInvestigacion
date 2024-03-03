from django.urls import path
from .views import *


urlpatterns = [
    path(
        "contents/<str:subject_name>",
        SubjectContentsView.as_view(),
        name="subject_contents",
    )
]
