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


class ExerciseSerializerCreateDocumentation(serializers.ModelSerializer):
    problem_statement = serializers.CharField(write_only=True)
    example = serializers.CharField(write_only=True, required=False)
    use_cases = serializers.ListField(
        child=serializers.JSONField(), write_only=True, required=False
    )

    class Meta:
        model = Exercise
        exclude = ["date", "user"]
