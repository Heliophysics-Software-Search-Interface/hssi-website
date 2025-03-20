import uuid
from django.db import models

# we need to import the softwares type for intellisense
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .softwares import Softwares

class Persons(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    lastName = models.CharField(max_length=100, null=True, blank=True)
    identifier = models.CharField(max_length=200, blank=True, null=True)
    affiliation = models.ForeignKey(
        'Organizations', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='persons'
    )

    # specified for intellisense, defined in Softwares model
    softwares: models.Manager['Softwares']

    class Meta: ordering = ['lastName', 'name']
    def __str__(self): return self.name