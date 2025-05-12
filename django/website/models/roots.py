import uuid
from django.db import models
from colorful.fields import RGBColorField

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .people import Person
    from .auxillary_info import Functionality, Award, RelatedItem

# Character length limits
LEN_NAME = 100
LEN_ABBREVIATION = 5

# Whether an entry in InstrumentObservatory is an instrument or an observatory
class InstrObsType(models.IntegerChoices):
    INSTRUMENT = 1, "Instrument"
    OBSERVATORY = 2, "Observatory"
    UNKNOWN = 3, "Unknown"

class HssiModel(models.Model):
    '''Base class for all models in the HSSI project'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    def get_search_terms(self) -> list[str]: 
        '''
        The search terms that are used for filtering autocomplete suggestions in 
        relevant form interfaces
        '''
        return [str(self)]

    class Meta:
        abstract = True

## Simple Root Models ----------------------------------------------------------
    
class OperatingSystem(HssiModel):
    '''Operating system on which the software can run'''
    name = models.CharField(max_length=LEN_NAME)

    class Meta: ordering = ['name']
    def __str__(self): return self.name

class Phenomena(HssiModel):
    '''Solar phenomena that relate to the software'''
    name = models.CharField(max_length=LEN_NAME)
    
    class Meta: ordering = ['name']
    def __str__(self): return self.name

class Keyword(HssiModel):
    name = models.CharField(max_length=LEN_NAME)

    class Meta: ordering = ['name']
    def __str__(self): return self.name

class Image(HssiModel):
    '''Reference to an image file and alt text description'''
    url = models.URLField(blank=True, null=True)
    description = models.CharField(max_length=250)

    class Meta: ordering = ['description']
    def __str__(self): return self.url

class ProgrammingLanguage(HssiModel):
    '''Primary Programming language used to develop the software'''
    name = models.CharField(max_length=LEN_NAME)
    version = models.CharField(max_length=LEN_NAME, blank=True, null=True)

    class Meta: ordering = ['name']
    def __str__(self): return self.name + (f" {self.version}" if self.version else "")

class DataInput(HssiModel):
    '''Ways that the software can accept data as input'''
    name = models.CharField(max_length=LEN_NAME)
    abbreviation = models.CharField(max_length=LEN_ABBREVIATION, blank=True, null=True)

    class Meta: ordering = ['name']
    def __str__(self): return self.name

class FileFormat(HssiModel):
    '''File formats that are supported as input or output types by the software'''
    name = models.CharField(max_length=LEN_NAME, blank=True, null=True)
    extension = models.CharField(max_length=25, blank=False, null=False)

    class Meta: ordering = ['name']
    def __str__(self): return self.extension + f" ({self.name})" if self.name else ""

class Region(HssiModel):
    '''Region of the sun which relates to the software'''
    name = models.CharField(max_length=LEN_NAME)

    class Meta: ordering = ['name']
    def __str__(self): return self.name

class InstrumentObservatory(HssiModel):
    '''An observatory or scientific research instrument'''
    type = models.IntegerField(choices=InstrObsType.choices, default=InstrObsType.UNKNOWN)
    name = models.CharField(max_length=LEN_NAME)
    identifier = models.URLField(blank=True, null=True)

    class Meta: ordering = ['name']
    def __str__(self): return self.name

## Complex Root Models ---------------------------------------------------------

class RepoStatus(HssiModel):
    '''
    Repo status as defined by the repostatus.org json-ld: 
    https://www.repostatus.org/badges/latest/ontology.jsonld
    '''
    identifier = models.URLField(blank=True, null=True)
    prefLabel = models.CharField(max_length=LEN_NAME, blank=False, null=False)
    definition = models.TextField(blank=True, null=True)
    image = models.URLField(blank=True, null=True)

    class Meta: 
        ordering = ['prefLabel']
        verbose_name_plural = "Repo Statuses"
    def __str__(self): return self.prefLabel

class FunctionCategory(HssiModel):
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

class License(HssiModel):
    name = models.CharField(max_length=100)
    identifier = models.CharField(max_length=100, blank=True, null=True)
    full_text = models.TextField(blank=True, null=True)
    scheme = models.CharField(max_length=100, blank=True, null=True)
    scheme_url = models.URLField(blank=True, null=True)
    url = models.URLField(blank=True, null=True)

    # specified for intellisense, defined in other models
    relatedItems: models.Manager['RelatedItem']

    class Meta: ordering = ['identifier', 'name']
    def __str__(self): return self.identifier or self.name

class Organization(HssiModel):
    '''A legal entity such as university, agency, or company'''

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

    def get_search_terms(self) -> list[str]:
        return [
            self.name,
            self.abbreviation
        ]

    class Meta: ordering = ['name']
    def __str__(self): 
        if self.abbreviation:
            return f"{self.name} ({self.abbreviation})"
        return self.name