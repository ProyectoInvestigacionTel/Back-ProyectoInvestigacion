from rest_framework import serializers
from exercise.use_case.models import UseCase
from exercise.use_case.serializers import UseCaseSerializer
from exercise.aux_func_views import (
    get_all_exercises_files,
    save_exercise_file,
    update_subject_contents,
)
from subject.models import Subject
from .models import *
from django.contrib.auth import get_user_model


class ExerciseSerializerCreate(serializers.ModelSerializer):
    problem_statement = serializers.CharField(write_only=True)
    example = serializers.CharField(write_only=True, required=False)
    use_cases = serializers.ListField(
        child=serializers.JSONField(), write_only=True, required=False
    )

    class Meta:
        model = Exercise
        exclude = [
            "date",
        ]

    def create(self, validated_data):
        problem_statement_text = validated_data.pop("problem_statement", None)
        example_text = validated_data.pop("example", None)
        use_cases_data = validated_data.pop("use_cases", None)

        exercise = Exercise.objects.create(**validated_data)

        subject_instance = Subject.objects.get(name=exercise.subject)
        new_contents = validated_data.get("contents", "")
        update_subject_contents(subject_instance, new_contents)

        if problem_statement_text:
            save_exercise_file(exercise, problem_statement_text, "problem_statement")
        if example_text:
            save_exercise_file(exercise, example_text, "example")

        if use_cases_data:
            for use_case_data in use_cases_data:
                UseCase.objects.create(exercise=exercise, **use_case_data)

        return exercise


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

        subject_instance = Subject.objects.get(name=exercise.subject)
        new_contents = validated_data.get("contents", "")
        update_subject_contents(subject_instance, new_contents)

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

        subject_instance = Subject.objects.get(name=instance.subject)
        new_contents = validated_data.get("contents", "")
        update_subject_contents(subject_instance, new_contents)

        if problem_statement_text:
            save_exercise_file(instance, problem_statement_text, "problem_statement")
        if example_text:
            save_exercise_file(instance, example_text, "example")

        if use_cases_data:
            for use_case_data in use_cases_data:
                UseCase.objects.create(exercise_id=instance, **use_case_data)
        return instance


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
    success_rate = serializers.SerializerMethodField()
    user_attempts_info = serializers.SerializerMethodField()

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

    def get_success_rate(self, obj):
        total_attempts = AttemptDetail.objects.filter(general_attempt_id__exercise_id=obj).count()
        successful_attempts = AttemptDetail.objects.filter(general_attempt_id__exercise_id=obj, result=True).count()

        print("total_attempts", total_attempts, flush=True)
        print("successful_attempts", successful_attempts, flush=True)
        
        if total_attempts > 0:
            success_rate = (successful_attempts / total_attempts) * 100
            return success_rate
        else:
            return 0

    def get_user_attempts_info(self, obj):
        user = self.context.get("request").user
        print("sdasdasdsadasda", user, flush=True)
        attempt_details = AttemptDetail.objects.filter(
            general_attempt_id__in=AttemptExercise.objects.filter(
                user_id=user, exercise_id=obj
            )
        )
        total_attempts = attempt_details.count()
        successful_attempts = attempt_details.filter(result=True).count()
        resolved = successful_attempts > 0

        return {
            "resolved": resolved,
            "total_attempts": total_attempts,
            "successful_attempts": successful_attempts,
        }


class AttemptExerciseGPTSerializer(serializers.ModelSerializer):
    exercise_id = serializers.PrimaryKeyRelatedField(queryset=Exercise.objects.all())
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all()
    )
    time = serializers.CharField(default="10:00:00")
    code = serializers.CharField(default='print("Hello World")', write_only=True)
    initial_feedback = serializers.CharField(
        default="initial feedback", write_only=True
    )
    attempts = serializers.IntegerField(default=0, write_only=True)

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


class AttemptExerciseSerializer(serializers.ModelSerializer):
    exercise_id = serializers.PrimaryKeyRelatedField(queryset=Exercise.objects.all())
    time = serializers.CharField(default="10:00:00")
    code = serializers.CharField(default='print("Hello World")', write_only=True)

    def create(self, validated_data):
        validated_data.pop("code", None)
        return AttemptExercise.objects.create(**validated_data)

    class Meta:
        model = AttemptExercise
        fields = [
            "exercise_id",
            "time",
            "code",
        ]


class CodeExecutionSerializer(serializers.ModelSerializer):
    exercise_id = serializers.PrimaryKeyRelatedField(queryset=Exercise.objects.all())
    time = serializers.CharField(default="10:00:00")
    code = serializers.CharField(default='print("Hello World")', write_only=True)

    class Meta:
        model = AttemptExercise
        fields = [
            "exercise_id",
            "time",
            "code",
        ]


class AttemptSaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttemptExercise
        fields = "__all__"


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


class RankingPerSubjectSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=100)
    total_exercises = serializers.IntegerField()
    exercises_completed = serializers.IntegerField()
    average_score = serializers.FloatField()
    success_rate = serializers.FloatField()


class ExerciseRankingSerializer(serializers.Serializer):
    exercise_id = serializers.IntegerField()
    title = serializers.CharField()
    total_attempts = serializers.IntegerField()
    completion_rate = serializers.FloatField()
