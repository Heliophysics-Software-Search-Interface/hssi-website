import uuid
from django.db import models

class IvoaType(models.IntegerChoices):
    INSTRUMENT = 1, "Instrument"
    OBSERVATORY = 2, "Observatory"
    MISSION = 3, "Mission"

class IvoaEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.IntegerField(choices=IvoaType.choices, default=IvoaType.INSTRUMENT)
    name = models.CharField(max_length=100)
    identifier = models.CharField(max_length=200, blank=True, null=True)
    ivoaEntryId = models.CharField(max_length=200, blank=True, null=True)

    class Meta: 
        ordering = ['name']
        verbose_name_plural = "IVOA entries"
    def __str__(self): return self.name
