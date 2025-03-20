import uuid
from django.db import models
from colorful.fields import RGBColorField

class FunctionCategories(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=5, null=True, blank=True)
    backgroundColor = RGBColorField("Background Color", default="#FFFFFF", blank=True, null=True)
    textColor = RGBColorField("Text Color", default="#000000", blank=True, null=True)

    # specified for intellisense, defined in Functionalities model
    functionalities: models.Manager["Functionalities"]

    class Meta: ordering = ['name']
    def __str__(self): return self.name

class Functionalities(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(
        FunctionCategories, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='functionalities'
    )

    class Meta: ordering = ['name']
    def __str__(self): return self.name