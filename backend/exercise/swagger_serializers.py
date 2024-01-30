from rest_framework import serializers
from .models import *
class ExerciseSerializerCreateTeacherDocumentation(serializers.ModelSerializer):
    problem_statement = serializers.CharField(required=True)
    class Meta:
        model = Exercise
        fields = [
            "title",
            "subject",
            "problem_statement",
            "input_format",
            "constraints",
            "output_format",
        ]
