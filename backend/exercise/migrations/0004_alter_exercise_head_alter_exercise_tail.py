# Generated by Django 4.2.4 on 2024-02-02 02:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("exercise", "0003_exercise_programming_language_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="exercise",
            name="head",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="exercise",
            name="tail",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
