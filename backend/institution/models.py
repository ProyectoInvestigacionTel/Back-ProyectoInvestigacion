from django.db import models

# Create your models here.
class Institution(models.Model):
    class Meta:
        db_table = "institution"

    institution_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    phone = models.CharField(max_length=100)
    website = models.URLField(max_length=100)
    description = models.TextField()
    campus = models.JSONField()
    
    def __str__(self):
        return self.institution_id