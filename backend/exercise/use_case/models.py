from django.db import models
from exercise.models import Exercise


class UseCase(models.Model):
    exercise = models.ForeignKey(
        Exercise, related_name="use_cases", on_delete=models.CASCADE
    )
    input_code = models.TextField()
    output_code = models.TextField()
    strength = models.IntegerField(default=0)
    is_sample = models.BooleanField(default=False)
    explanation = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Use Case for Exercise: {self.exercise.title}"
