# Generated by Django 4.2.4 on 2024-01-26 00:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("exercise", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="usecase",
            old_name="input_data",
            new_name="input_code",
        ),
        migrations.RenameField(
            model_name="usecase",
            old_name="output_data",
            new_name="output_code",
        ),
    ]