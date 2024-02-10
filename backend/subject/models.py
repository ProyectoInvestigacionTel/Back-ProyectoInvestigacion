from django.db import models

class Subject(models.Model):
    class Meta:
        db_table = "subject"

    subject_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=30)
    description = models.TextField()
    contents = models.TextField()
    institution = models.ForeignKey(
        "institution.Institution", on_delete=models.DO_NOTHING, db_column="institution_id"
    )
    def __str__(self):
        return self.name