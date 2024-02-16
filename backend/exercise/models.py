from django.db import models
from django.contrib.auth import get_user_model


def code_directory_path(instance, filename):
    return "attempt_per_user/{0}/{1}/{2}/code_Re{2}_Ex{1}.txt".format(
        instance.attempt_id.general_attempt_id.user_id.email,
        instance.attempt_id.general_attempt_id.exercise_id.exercise_id,
        instance.feedback_id,
    )


def conversation_directory_path(instance, filename):
    return "attempt_per_user/{0}/{1}/{2}/conversation_Fe{2}_Ex{1}.json".format(
        instance.attempt_id.general_attempt_id.user_id.email,
        instance.attempt_id.general_attempt_id.exercise_id.exercise_id,
        instance.feedback_id,
    )


def result_use_cases_directory_path(instance, filename):
    return "attempt_per_user/{0}/{1}/{2}/result_use_cases_Fe{2}_Ex{1}.json".format(
        instance.attempt_id.general_attempt_id.user_id.email,
        instance.attempt_id.general_attempt_id.exercise_id.exercise_id,
        instance.feedback_id,
    )


def problem_statement_directory_path(instance, filename):
    return "exercises/temp/problem_statement_{0}".format(filename)


def example_directory_path(instance, filename):
    return "exercises/temp/example_{0}".format(filename)


class Exercise(models.Model):
    class Meta:
        db_table = "exercises"

    exercise_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, db_column="user_id"
    )
    date = models.DateTimeField(auto_now_add=True)
    problem_statement = models.FileField(
        upload_to=problem_statement_directory_path, null=True
    )
    example = models.FileField(upload_to=example_directory_path, null=True)
    difficulty = models.CharField(max_length=100)
    contents = models.CharField(max_length=100, null=True)
    score = models.PositiveSmallIntegerField(default=0)
    programming_language = models.CharField(max_length=20, default="Python")
    language = models.CharField(default="Spanish", max_length=20)
    subject = models.CharField(max_length=30)
    title = models.CharField(max_length=100)
    head = models.CharField(max_length=100, null=True, blank=True)
    tail = models.CharField(max_length=100, null=True, blank=True)
    binary = models.BooleanField(default=False)
    constraints = models.TextField()
    input_format = models.TextField()
    output_format = models.TextField()
    exercise_dependency = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.DO_NOTHING
    )
    is_visible = models.BooleanField(default=False)

    def __str__(self):
        return str(self.exercise_id)


class AttemptExercise(models.Model):
    class Meta:
        db_table = "attempts"

    general_attempt_id = models.AutoField(primary_key=True)
    exercise_id = models.ForeignKey(
        Exercise, on_delete=models.CASCADE, db_column="exercise_id"
    )
    user_id = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, db_column="user_id"
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    score = models.PositiveSmallIntegerField(default=0)
    time = models.CharField(max_length=20)
    result = models.BooleanField(default=False)


class AttemptDetail(models.Model):
    class Meta:
        db_table = "attempt_details"

    attempt_id = models.AutoField(primary_key=True)
    general_attempt_id = models.ForeignKey(
        AttemptExercise, on_delete=models.CASCADE, db_column="general_attempt_id"
    )

    date = models.DateTimeField()
    score = models.PositiveSmallIntegerField()
    result = models.BooleanField()
    feedback = models.PositiveSmallIntegerField()


class FeedbackDetail(models.Model):
    class Meta:
        db_table = "feedback_details"

    feedback_id = models.AutoField(primary_key=True)
    attempt_id = models.ForeignKey(
        AttemptDetail, on_delete=models.CASCADE, db_column="attempt_id"
    )
    conversation_file = models.FileField(
        upload_to=conversation_directory_path, null=True, blank=True
    )
    code_file = models.FileField(upload_to=code_directory_path, null=True, blank=True)
    result_file = models.FileField(
        upload_to=result_use_cases_directory_path, null=True, blank=True
    )
    stars = models.PositiveSmallIntegerField(default=0)
