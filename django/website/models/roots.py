import uuid
from django.db import models
from colorful.fields import RGBColorField

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .people import Person
    from .auxillary_info import Functionality, Award

# Character length limits
LEN_NAME = 100
LEN_ABBREVIATION = 5

# Whether an entry in InstrumentObservatory is an instrument or an observatory
class InstrObsType(models.IntegerChoices):
    INSTRUMENT = 1, "Instrument"
    OBSERVATORY = 2, "Observatory"
    UNKNOWN = 3, "Unknown"

## Simple Root Models ----------------------------------------------------------

class OperatingSystem(models.Model):
    '''Operating system on which the software can run'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=LEN_NAME)

    class Meta: ordering = ['name']
    def __str__(self): return self.name

class Phenomena(models.Model):
    '''Solar phenomena that relate to the software'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=LEN_NAME)
    
    class Meta: ordering = ['name']
    def __str__(self): return self.name

class Keyword(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=LEN_NAME)

    class Meta: ordering = ['name']
    def __str__(self): return self.name

class Image(models.Model):
    '''Reference to an image file and alt text description'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    url = models.URLField(blank=True, null=True)
    description = models.CharField(max_length=250)

    class Meta: ordering = ['description']
    def __str__(self): return self.url

class ProgrammingLanguage(models.Model):
    '''Primary Programming language used to develop the software'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=LEN_NAME)
    version = models.CharField(max_length=LEN_NAME, blank=True, null=True)

    class Meta: ordering = ['name']
    def __str__(self): return self.name + (f" {self.version}" if self.version else "")

class DataInput(models.Model):
    '''Ways that the software can accept data as input'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=LEN_NAME)
    abbreviation = models.CharField(max_length=LEN_ABBREVIATION, blank=True, null=True)

    class Meta: ordering = ['name']
    def __str__(self): return self.name

class FileFormat(models.Model):
    '''File formats that are supported as input or output types by the software'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=LEN_NAME, blank=True, null=True)
    extension = models.CharField(max_length=25, blank=False, null=False)

    class Meta: ordering = ['name']
    def __str__(self): return self.extension + f" ({self.name})" if self.name else ""

class Region(models.Model):
    '''Region of the sun which relates to the software'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=LEN_NAME)

    class Meta: ordering = ['name']
    def __str__(self): return self.name

class InstrumentObservatory(models.Model):
    '''An observatory or scientific research instrument'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.IntegerField(choices=InstrObsType.choices, default=InstrObsType.UNKNOWN)
    name = models.CharField(max_length=LEN_NAME)
    identifier = models.URLField(blank=True, null=True)

    class Meta: ordering = ['name']
    def __str__(self): return self.name

## Complex Root Models ---------------------------------------------------------

class RepoStatus(models.Model):
    '''
    Repo status as defined by the repostatus.org json-ld: 
    https://www.repostatus.org/badges/latest/ontology.jsonld
    '''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identifier = models.URLField(blank=True, null=True)
    prefLabel = models.CharField(max_length=LEN_NAME, blank=False, null=False)
    definition = models.TextField(blank=True, null=True)
    image = models.URLField(blank=True, null=True)

    class Meta: 
        ordering = ['prefLabel']
        verbose_name_plural = "Repo Statuses"
    def __str__(self): return self.prefLabel

class FunctionCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=5, null=True, blank=True)
    backgroundColor = RGBColorField("Background Color", default="#FFFFFF", blank=True, null=True)
    textColor = RGBColorField("Text Color", default="#000000", blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # specified for intellisense, defined in Functionalities model
    functionalities: models.Manager['Functionality']

    class Meta: 
        ordering = ['name']
        verbose_name_plural = "Function Categories"
    def __str__(self): return self.name

class License(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    identifier = models.CharField(max_length=100, blank=True, null=True)
    full_text = models.TextField(blank=True, null=True)
    scheme = models.CharField(max_length=100, blank=True, null=True)
    scheme_url = models.URLField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    class Meta: ordering = ['identifier', 'name']
    def __str__(self): return self.identifier or self.name

class Organization(models.Model):
    '''A legal entity such as university, agency, or company'''

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=LEN_NAME)
    abbreviation = models.CharField(max_length=20, null=True, blank=True)
    website = models.URLField(blank=True, null=True)
    identifier = models.URLField(blank=True, null=True)
    parent_organization = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='sub_organizations'
    )

    # specified for intellisense, defined in other models
    people: models.Manager['Person']
    awards: models.Manager['Award']

    class Meta: ordering = ['name']
    def __str__(self): 
        if self.abbreviation:
            return f"{self.name} ({self.abbreviation})"
        return self.name