# Generated by Django 4.2.4 on 2024-01-26 01:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("exercise", "0002_rename_input_data_usecase_input_code_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="exercise",
            name="programming_language",
            field=models.CharField(default="Python", max_length=20),
        ),
        migrations.AlterField(
            model_name="exercise",
            name="language",
            field=models.CharField(default="Spanish", max_length=20),
        ),
    ]
