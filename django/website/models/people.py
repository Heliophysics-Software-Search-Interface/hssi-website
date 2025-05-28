import uuid
from django.db import models

from .structurizer import form_config
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
    identifier = form_config(
        models.URLField(blank=True, null=True),
        label="Identifier",
        tooltipExplanation="The identifier of the person, such as the ORCiD.",
        tooltipBestPractise="Please enter the complete identifier, e.g. https://orcid.org/0000-0003-0875-2023."
    )
    affiliation = form_config(
        models.ManyToManyField(
            Organization, 
            blank=True, 
            related_name='people'
        ),
        label="Affiliation",
        tooltipExplanation="The affiliation of the person, such as an institution or other entity.",
        tooltipBestPractise="Please enter the complete name of the affiliated entity without using acronyms (e.g. Center for Astrophysics Harvard & Smithsonian). If more than one affiliation, please enter them separately.",
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

    @classmethod
    def get_top_field(cls) -> models.Field: return cls._meta.get_field("firstName")

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
    email = form_config(
        models.EmailField(null=False, blank=False),
        label="Email",
        tooltipExplanation="The work email address of the person who reviewed the metadata.",
        tooltipBestPractise="Please ensure that a complete email address is given.",
    )
    person = form_config(
        models.OneToOneField(
            Person, 
            on_delete=models.CASCADE, 
            null=False, blank=False, 
            related_name='curator'
        ),
        label="Curator",
        tooltipExplanation="The name of the person(s) who reviewed the metadata.",
        tooltipBestPractise="Given name, initials and last/surname (e.g. Jack L. Doe).",
    )

    # specified for intellisense, defined in other models
    submission_infos: models.Manager['SubmissionInfo']
    submission_infos_led: models.Manager['SubmissionInfo']

    @classmethod
    def get_top_field(cls) -> models.Field: return cls._meta.get_field("email")

    class Meta: ordering = ['person']
    def __str__(self): return str(self.person)

class Submitter(HssiModel):
    '''A person who has submitted a software'''
    email = form_config(
        models.EmailField(null=False, blank=False),
        label="Email",
        tooltipExplanation="The work email address of the metadata record submitter.",
        tooltipBestPractise="Please ensure that a complete email address is given.",
    )
    person = form_config(
        models.ForeignKey(
            Person, 
            on_delete=models.CASCADE,
            null=False, blank=False, 
            related_name='submitter'
        ),
        label="Submitter",
        tooltipExplanation="The name of the person who submitted the metadata.",
        tooltipBestPractise="Given name, initials and last/surname (e.g. Jack L. Doe).",
    )

    # specified for intellisense, defined in other models
    submission_infos: models.Manager['SubmissionInfo']

    @classmethod
    def get_top_field(cls) -> models.Field: return cls._meta.get_field("email")
    
    class Meta: ordering = ['person']
    def __str__(self): return str(self.person)