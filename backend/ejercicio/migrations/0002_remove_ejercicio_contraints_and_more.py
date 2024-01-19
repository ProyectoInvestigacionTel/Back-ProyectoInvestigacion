# Generated by Django 4.2.4 on 2024-01-19 21:10

from django.db import migrations, models
import django.db.models.deletion
import ejercicio.models


class Migration(migrations.Migration):

    dependencies = [
        ("ejercicio", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="ejercicio",
            name="contraints",
        ),
        migrations.RemoveField(
            model_name="ejercicio",
            name="descripcion",
        ),
        migrations.RemoveField(
            model_name="ejercicio",
            name="resumen",
        ),
        migrations.AddField(
            model_name="ejercicio",
            name="dependencia_ejercicio",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.DO_NOTHING,
                to="ejercicio.ejercicio",
            ),
        ),
        migrations.AddField(
            model_name="ejercicio",
            name="visible",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="ejercicio",
            name="contenidos",
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="ejercicio",
            name="ejemplo_file",
            field=models.FileField(
                null=True, upload_to=ejercicio.models.ejemplo_directory_path
            ),
        ),
        migrations.AlterField(
            model_name="ejercicio",
            name="head",
            field=models.CharField(max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="ejercicio",
            name="puntaje",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="ejercicio",
            name="salida_file",
            field=models.FileField(
                null=True, upload_to=ejercicio.models.salida_directory_path
            ),
        ),
        migrations.AlterField(
            model_name="ejercicio",
            name="tail",
            field=models.CharField(max_length=100, null=True),
        ),
    ]
