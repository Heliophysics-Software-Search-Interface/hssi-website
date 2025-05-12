import uuid
from django.db import models

from .people import Person
from .roots import HssiModel, Organization, FunctionCategory, License, LEN_NAME

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

    class Meta: ordering = ['name']
    def __str__(self): return self.name

class Functionality(HssiModel):
    '''A type of functionality supported by the software'''
    name = models.CharField(max_length=LEN_NAME)
    abbreviation = models.CharField(max_length=5, blank=True, null=True)
    category = models.ForeignKey(
        FunctionCategory, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='functionalities'
    )

    class Meta: 
        ordering = ['name']
        verbose_name_plural = "Functionalities"
    def __str__(self): return self.name

class RelatedItem(HssiModel):
    name = models.CharField(max_length=LEN_NAME, blank=False, null=False)
    identifier = models.URLField(blank=True, null=True)
    authors = models.ManyToManyField(
        Person,
        blank=True,
        related_name='datasets'
    )
    creditText = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    license = models.ForeignKey(
        License,
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='datasets'
    )
    
    class Meta: ordering = ['name']
    def __str__(self): return self.name