# Generated by Django 5.0.1 on 2024-02-09 00:29

import django.db.models.deletion
import exercise.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AttemptExercise",
            fields=[
                (
                    "general_attempt_id",
                    models.AutoField(primary_key=True, serialize=False),
                ),
                ("attempts", models.PositiveSmallIntegerField(default=0)),
                ("score", models.PositiveSmallIntegerField(default=0)),
                ("time", models.CharField(max_length=20)),
                ("result", models.BooleanField(default=False)),
                (
                    "user_id",
                    models.ForeignKey(
                        db_column="user_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "attempts",
            },
        ),
        migrations.CreateModel(
            name="AttemptDetail",
            fields=[
                ("attempt_id", models.AutoField(primary_key=True, serialize=False)),
                ("date", models.DateTimeField()),
                ("score", models.PositiveSmallIntegerField()),
                ("result", models.BooleanField()),
                ("feedback", models.PositiveSmallIntegerField()),
                (
                    "general_attempt_id",
                    models.ForeignKey(
                        db_column="general_attempt_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="exercise.attemptexercise",
                    ),
                ),
            ],
            options={
                "db_table": "attempt_details",
            },
        ),
        migrations.CreateModel(
            name="Exercise",
            fields=[
                ("exercise_id", models.AutoField(primary_key=True, serialize=False)),
                ("date", models.DateTimeField(auto_now_add=True)),
                (
                    "problem_statement",
                    models.FileField(
                        null=True,
                        upload_to=exercise.models.problem_statement_directory_path,
                    ),
                ),
                (
                    "example",
                    models.FileField(
                        null=True, upload_to=exercise.models.example_directory_path
                    ),
                ),
                ("difficulty", models.CharField(max_length=100)),
                ("contents", models.CharField(max_length=100, null=True)),
                ("score", models.PositiveSmallIntegerField(default=0)),
                (
                    "programming_language",
                    models.CharField(default="Python", max_length=20),
                ),
                ("language", models.CharField(default="Spanish", max_length=20)),
                ("subject", models.CharField(max_length=30)),
                ("title", models.CharField(max_length=100)),
                ("head", models.CharField(blank=True, max_length=100, null=True)),
                ("tail", models.CharField(blank=True, max_length=100, null=True)),
                ("binary", models.BooleanField(default=False)),
                ("constraints", models.TextField()),
                ("input_format", models.TextField()),
                ("output_format", models.TextField()),
                ("is_visible", models.BooleanField(default=False)),
                (
                    "exercise_dependency",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.DO_NOTHING,
                        to="exercise.exercise",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        db_column="user_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "exercises",
            },
        ),
        migrations.AddField(
            model_name="attemptexercise",
            name="exercise_id",
            field=models.ForeignKey(
                db_column="exercise_id",
                on_delete=django.db.models.deletion.CASCADE,
                to="exercise.exercise",
            ),
        ),
        migrations.CreateModel(
            name="FeedbackDetail",
            fields=[
                ("feedback_id", models.AutoField(primary_key=True, serialize=False)),
                (
                    "conversation_file",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to=exercise.models.conversation_directory_path,
                    ),
                ),
                (
                    "code_file",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to=exercise.models.code_directory_path,
                    ),
                ),
                (
                    "result_file",
                    models.FileField(
                        blank=True,
                        null=True,
                        upload_to=exercise.models.result_use_cases_directory_path,
                    ),
                ),
                ("stars", models.PositiveSmallIntegerField(default=0)),
                (
                    "attempt_id",
                    models.ForeignKey(
                        db_column="attempt_id",
                        on_delete=django.db.models.deletion.CASCADE,
                        to="exercise.attemptdetail",
                    ),
                ),
            ],
            options={
                "db_table": "feedback_details",
            },
        ),
        migrations.CreateModel(
            name="UseCase",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("input_code", models.TextField()),
                ("output_code", models.TextField()),
                ("strength", models.IntegerField(default=0)),
                ("is_sample", models.BooleanField(default=False)),
                ("explanation", models.TextField(blank=True, null=True)),
                (
                    "exercise",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="use_cases",
                        to="exercise.exercise",
                    ),
                ),
            ],
        ),
    ]
