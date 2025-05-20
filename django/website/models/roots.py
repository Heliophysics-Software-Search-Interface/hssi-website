import uuid
from django.db import models
from colorful.fields import RGBColorField

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .people import Person
    from .auxillary_info import Functionality, Award, RelatedItem

# Character length limits
LEN_LONGNAME = 512
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

    def get_tooltip(self) -> str: return ""

    class Meta:
        abstract = True

class ControlledList(HssiModel):
    '''Base class for all controlled lists in the HSSI project'''
    name = models.CharField(max_length=LEN_NAME, blank=False, null=False)
    identifier = models.URLField(blank=True, null=True)
    definition = models.TextField(blank=True, null=True)

    def __str__(self): return self.name

    def get_tooltip(self): return self.definition

    class Meta:
        ordering = ['name']
        abstract = True

## Simple Root Models ----------------------------------------------------------

class Keyword(ControlledList): pass

class OperatingSystem(ControlledList):
    '''Operating system on which the software can run'''
    pass

class Phenomena(ControlledList):
    '''Solar phenomena that relate to the software'''
    pass

class RepoStatus(ControlledList):
    '''
    Repo status as defined by the repostatus.org json-ld: 
    https://www.repostatus.org/badges/latest/ontology.jsonld
    '''
    image = models.URLField(blank=True, null=True)

    class Meta: verbose_name_plural = "Repo Statuses"

class Image(HssiModel):
    '''Reference to an image file and alt text description'''
    url = models.URLField(blank=True, null=True)
    description = models.CharField(max_length=250)

    class Meta: ordering = ['description']
    def __str__(self): return self.url

class ProgrammingLanguage(ControlledList):
    '''Primary Programming language used to develop the software'''
    version = models.CharField(max_length=LEN_NAME, blank=True, null=True)

    def __str__(self): return self.name + (f" {self.version}" if self.version else "")

class DataInput(ControlledList):
    '''Ways that the software can accept data as input'''
    abbreviation = models.CharField(max_length=LEN_ABBREVIATION, blank=True, null=True)

    def __str__(self): return self.name

class FileFormat(ControlledList):
    '''File formats that are supported as input or output types by the software'''
    extension = models.CharField(max_length=25, blank=False, null=False)

    def __str__(self): return self.extension + f" ({self.name})" if self.name else ""

class Region(ControlledList):
    '''Region of the sun which relates to the software'''
    class Meta: ordering = ['name']
    def __str__(self): return self.name

class InstrumentObservatory(HssiModel):
    '''An observatory or scientific research instrument'''
    type = models.IntegerField(choices=InstrObsType.choices, default=InstrObsType.UNKNOWN)
    name = models.CharField(max_length=LEN_LONGNAME)
    abbreviation = models.CharField(max_length=LEN_NAME, null=True, blank=True)
    identifier = models.URLField(blank=True, null=True)

    def get_search_terms(self) -> list[str]:
        terms = []
        if self.abbreviation:
            terms.append(self.abbreviation)
        terms.extend(self.name.split(' '))
        return terms
    
    class Meta: ordering = ['name']
    def __str__(self): 
        return f"{self.name} ({self.abbreviation})" if self.abbreviation else self.name

## Complex Root Models ---------------------------------------------------------

class FunctionCategory(ControlledList):
    abbreviation = models.CharField(max_length=5, null=True, blank=True)
    backgroundColor = RGBColorField("Background Color", default="#FFFFFF", blank=True, null=True)
    textColor = RGBColorField("Text Color", default="#000000", blank=True, null=True)

    # specified for intellisense, defined in Functionalities model
    functionalities: models.Manager['Functionality']

    class Meta: verbose_name_plural = "Function Categories"
    def __str__(self): return self.name

class License(HssiModel):
    name = models.CharField(max_length=LEN_NAME)
    url = models.URLField(blank=True, null=True)

    # specified for intellisense, defined in other models
    relatedItems: models.Manager['RelatedItem']

    class Meta: ordering = ['name']
    def __str__(self): return self.name

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