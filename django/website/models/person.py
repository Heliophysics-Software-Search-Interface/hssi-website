import uuid
from django.db import models

# we need to import the softwares type for intellisense
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .software import Software
    from .submission_info import SubmissionInfo

class Person(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    lastName = models.CharField(max_length=100, null=True, blank=True)
    identifier = models.CharField(max_length=512, blank=True, null=True)
    affiliation = models.ForeignKey(
        'Organization', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='persons'
    )

    # specified for intellisense, defined in other models
    softwares: models.Manager['Software']
    submission_info: models.Manager['SubmissionInfo']

    class Meta: ordering = ['lastName', 'name']
    def __str__(self): return self.name

class Curator(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=100)
    person = models.ForeignKey(
        Person, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='curators'
    )

    # specified for intellisense, defined in other models
    submission_info_owner: models.Manager['SubmissionInfo']
    submission_info_leader: models.Manager['SubmissionInfo']

    class Meta: 
        ordering = ['person']
        verbose_name_plural = "People"
    def __str__(self): return str(self.person)
