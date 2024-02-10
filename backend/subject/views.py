from rest_framework.response import Response
from rest_framework.views import APIView
from subject.models import Subject
from rest_framework import status


class SubjectContentsView(APIView):
    def get(self, request, subject_name):
        try:
            subject = Subject.objects.get(name=subject_name)
            return Response(
                {
                    "name": subject.name,
                    "description": subject.description,
                    "contents": subject.contents,
                },
                status=status.HTTP_200_OK,
            )
        except Subject.DoesNotExist:
            return Response(
                {"error": "Subject not found"}, status=status.HTTP_404_NOT_FOUND
            )
