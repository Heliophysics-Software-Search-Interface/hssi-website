import uuid
from django.db import models

from .people import Person
from .roots import (
    HssiModel, ControlledList, Organization, FunctionCategory, 
    License, LEN_NAME
)

from typing import Callable

class RelatedItemType(models.IntegerChoices):
    '''The type of an object in the RelatedField model'''
    SOFTWARE = 1, "Software"
    DATASET = 2, "Dataset"
    PUBLICATION = 3, "Publication"
    UNKNOWN = 4, "Unknown"

## -----------------------------------------------------------------------------

class Award(HssiModel):
    '''A grant or other funding award given by an organization'''
    name = models.CharField(max_length=LEN_NAME)
    identifier = models.URLField(blank=True, null=True)
    funder = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='awards'
    )

    @classmethod
    def get_top_field(cls) -> models.Field: return cls._meta.get_field("name")

    class Meta: ordering = ['name']
    def __str__(self): return self.name

class Functionality(ControlledList):
    '''A type of functionality supported by the software'''
    abbreviation = models.CharField(max_length=5, blank=True, null=True)
    category = models.ForeignKey(
        FunctionCategory, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='functionalities'
    )

    class Meta: verbose_name_plural = "Functionalities"
    def __str__(self): return self.name

class RelatedItem(ControlledList):
    type = models.IntegerField(
        choices=RelatedItemType.choices, 
        default=RelatedItemType.UNKNOWN
    )
    identifier = models.URLField(blank=True, null=True)
    authors = models.ManyToManyField(
        Person,
        blank=True,
        related_name='relatedItems'
    )
    creditText = models.TextField(blank=True, null=True)
    license = models.ForeignKey(
        License,
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='relatedItems'
    )

    # specified for intellisense, defined automatically by django
    get_type_display: Callable[[], str]
    
    def __str__(self): return f"{self.name} ({self.get_type_display()})"