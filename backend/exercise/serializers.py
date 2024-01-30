from rest_framework import serializers

from exercise.aux_func_views import get_all_exercises_files, save_exercise_file
from .models import *

from django.contrib.auth import get_user_model


class ExerciseSerializerCreate(serializers.ModelSerializer):
    problem_statement = serializers.FileField(required=True)
    use_case = serializers.FileField(required=True)
    example_file = serializers.FileField(required=False)
    output_file = serializers.FileField(required=False)
    difficulty = serializers.CharField(required=True)

    class Meta:
        model = Exercise
        exclude = [
            "date",
        ]


class ExerciseSerializerCreateTeacher(serializers.ModelSerializer):
    problem_statement = serializers.CharField(write_only=True)

    class Meta:
        model = Exercise
        fields = [
            "title",
            "subject",
            "problem_statement",
            "input_format",
            "constraints",
            "output_format",
            "user",
        ]

    def create(self, validated_data):
        problem_statement_text = validated_data.pop("problem_statement", None)
        exercise = Exercise.objects.create(**validated_data)

        save_exercise_file(exercise, problem_statement_text, "problem_statement")

        return exercise


class ExerciseSerializerUpdateTeacher(serializers.ModelSerializer):
    # algunos es para que en swagger no aparezcan como required
    problem_statement = serializers.CharField(required=False)
    subject = serializers.CharField(required=False)
    problem_statement = serializers.CharField(required=False)
    constraints = serializers.CharField(required=False)
    input_format = serializers.CharField(required=False)
    difficulty = serializers.CharField(required=False)
    output_format = serializers.CharField(required=False)
    user = serializers.CharField(required=False)
    title = serializers.CharField(required=False)
    use_cases = serializers.ListField(
        child=serializers.JSONField(), write_only=True, required=False
    )

    class Meta:
        model = Exercise
        fields = "__all__"

    def update(self, instance, validated_data):
        problem_statement_text = validated_data.pop("problem_statement", None)
        example_text = validated_data.pop("example", None)
        use_cases_data = validated_data.pop("use_cases", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if problem_statement_text:
            save_exercise_file(instance, problem_statement_text, "problem_statement")
        if example_text:
            save_exercise_file(instance, example_text, "example")
        if use_cases_data:
            for use_case_data in use_cases_data:
                UseCase.objects.create(exercise=instance, **use_case_data)
        return instance


class UseCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = UseCase
        fields = ("input_code", "output_code", "strength", "is_sample", "explanation")


class ExerciseSerializerView(serializers.ModelSerializer):
    use_cases = serializers.SerializerMethodField()
    files_data = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        exclude = [
            "problem_statement",
            "example",
        ]

    def get_files_data(self, obj):
        return get_all_exercises_files(obj.exercise_id, None)

    def get_use_cases(self, obj):
        use_cases = UseCase.objects.filter(exercise=obj)
        return UseCaseSerializer(use_cases, many=True).data


class ExerciseListSerializerAll(serializers.ModelSerializer):
    files_data = serializers.SerializerMethodField()
    use_cases = serializers.SerializerMethodField()

    class Meta:
        model = Exercise
        exclude = [
            "problem_statement",
            "example",
        ]

    def get_files_data(self, obj):
        return get_all_exercises_files(obj.exercise_id, None)

    def get_use_cases(self, obj):
        use_cases = UseCase.objects.filter(exercise=obj)
        return UseCaseSerializer(use_cases, many=True).data


class AttemptExerciseSerializer(serializers.ModelSerializer):
    exercise_id = serializers.PrimaryKeyRelatedField(queryset=Exercise.objects.all())
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all()
    )
    time = serializers.CharField(default="10:00:00")
    code = serializers.CharField(default='print("Hello World")', write_only=True)
    initial_feedback = serializers.CharField(
        default="initial feedback", write_only=True
    )

    def create(self, validated_data):
        validated_data.pop("code", None)
        validated_data.pop("initial_feedback", None)
        return AttemptExercise.objects.create(**validated_data)

    class Meta:
        model = AttemptExercise
        fields = [
            "exercise_id",
            "user_id",
            "time",
            "code",
            "initial_feedback",
            "attempts",
        ]


class AttemptDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttemptDetail
        fields = "__all__"


class FeedbackDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackDetail
        fields = "__all__"


class MessageSerializer(serializers.Serializer):
    sender = serializers.CharField(max_length=100)
    message = serializers.CharField()


class conversationSerializer(serializers.Serializer):
    mensajes = MessageSerializer(many=True)


class UseCaseBulkCreateSerializer(serializers.Serializer):
    use_cases = UseCaseSerializer(many=True)

    def create(self, validated_data):
        use_cases_data = validated_data.pop("use_cases")
        use_cases = [
            UseCase.objects.create(**use_case_data) for use_case_data in use_cases_data
        ]
        return use_cases
