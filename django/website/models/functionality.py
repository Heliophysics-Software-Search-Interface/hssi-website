import uuid
from django.db import models
from colorful.fields import RGBColorField

class FunctionCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=5, null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    backgroundColor = RGBColorField("Background Color", default="#FFFFFF", blank=True, null=True)
    textColor = RGBColorField("Text Color", default="#000000", blank=True, null=True)

    # specified for intellisense, defined in Functionalities model
    functionalities: models.Manager["Functionality"]

    class Meta: 
        ordering = ['name']
        verbose_name_plural = "Function Categories"
    def __str__(self): return self.name

class Functionality(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=5, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(
        FunctionCategory, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='functionalities'
    )

    class Meta: 
        ordering = ['name']
        verbose_name_plural = "Functionalities"
    def __str__(self): return self.name
