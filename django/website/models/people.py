import uuid
from django.db import models

from .roots import Organization, LEN_NAME

# we need to import the softwares type for intellisense
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .software import Software
    from .submission_info import SubmissionInfo

class Person(models.Model):
    '''Metadata to hold needed information about someone'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firstName = models.CharField(max_length=LEN_NAME, null=False, blank=False)
    lastName = models.CharField(max_length=LEN_NAME, null=False, blank=False)
    identifier = models.URLField(blank=True, null=True)
    affiliation = models.ManyToManyField(
        Organization, 
        null=True, 
        blank=True, 
        related_name='people'
    )

    # specified for intellisense, defined in other models
    softwares: models.Manager['Software']
    submission_info: models.Manager['SubmissionInfo']
    curator: models.Manager['Curator']

    class Meta: 
        ordering = ['lastName', 'firstName']
        verbose_name_plural = "People"
    def __str__(self): return self.name + ("" if self.lastName == None else " " + self.lastName)

    def to_str_lastname_firstname(self) -> str:
        if self.lastName is None or len(self.lastName) <= 0:
            return self.name
        return f"{self.lastName}, {self.firstName}"

class Curator(models.Model):
    '''A user who is able to curate submissions'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(null=False, blank=False)
    person = models.OneToOneField(
        Person, 
        on_delete=models.CASCADE, 
        null=False, blank=False, 
        related_name='curator'
    )

    # specified for intellisense, defined in other models
    submission_infos: models.Manager['SubmissionInfo']
    submission_infos_led: models.Manager['SubmissionInfo']

    class Meta: ordering = ['person']
    def __str__(self): return str(self.person)

class Submitter(models.Model):
    '''A person who has submitted a software'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(null=False, blank=False)
    person = models.ForeignKey(
        Person, 
        on_delete=models.CASCADE, 
        null=False, blank=False, 
        related_name='submitter'
    )

    # specified for intellisense, defined in other models
    submission_infos: models.Manager['SubmissionInfo']

    class Meta: ordering = ['person']
    def __str__(self): return str(self.person)