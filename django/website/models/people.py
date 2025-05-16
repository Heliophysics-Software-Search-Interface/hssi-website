import uuid
from django.db import models

from .roots import HssiModel, Organization, LEN_NAME

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .auxillary_info import RelatedItem

# we need to import the softwares type for intellisense
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .software import Software
    from .submission_info import SubmissionInfo

class Person(HssiModel):
    '''Metadata to hold needed information about someone'''
    firstName = models.CharField(max_length=LEN_NAME, null=False, blank=False, default="")
    lastName = models.CharField(max_length=LEN_NAME, null=False, blank=False, default="")
    identifier = models.URLField(blank=True, null=True)
    affiliation = models.ManyToManyField(
        Organization, 
        blank=True, 
        related_name='people'
    )

    # specified for intellisense, defined in other models
    softwares: models.Manager['Software']
    submission_info: models.Manager['SubmissionInfo']
    curator: models.Manager['Curator']
    relatedItems: models.Manager['RelatedItem']

    # meta info that allows data in this model to be serialized to allow for user discovery
    def get_search_terms(self) -> list[str]:
        return [
            self.firstName,
            self.lastName,
            self.identifier
        ]

    class Meta: 
        ordering = ['lastName', 'firstName']
        verbose_name_plural = 'People'
    def __str__(self): return self.firstName + " " + self.lastName

    def to_str_lastname_firstname(self) -> str:
        if self.lastName is None or len(self.lastName) <= 0:
            return self.firstName
        return f"{self.lastName}, {self.firstName}"

class Curator(HssiModel):
    '''A user who is able to curate submissions'''
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

class Submitter(HssiModel):
    '''A person who has submitted a software'''
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