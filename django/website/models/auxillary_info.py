import uuid
from django.db import models

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .software import Software

from .people import Person
from .roots import Organization, FunctionCategory, License, LEN_NAME

## -----------------------------------------------------------------------------

class Award(models.Model):
    '''A grant or other funding award given by an organization'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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

class Functionality(models.Model):
    '''A type of functionality supported by the software'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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

class Dataset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=LEN_NAME, blank=False, null=False)
    creator = models.ManyToManyField(
        Person,
        blank=True,
        related_name='datasets'
    )
    description = models.TextField(blank=True, null=True)
    license = models.ForeignKey(
        License,
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='datasets'
    )
    creditText = models.TextField(blank=True, null=True)
    identifier = models.URLField(blank=True, null=True)
    
    class Meta: ordering = ['name']
    def __str__(self): return self.name

class SoftwareVersion(models.Model):
    '''A snapshot of the software metadata whenever it's updated to a new version'''
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    number = models.CharField(max_length=LEN_NAME)
    release_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    version_pid = models.URLField(blank=True, null=True)
    software = models.ForeignKey(
        'Software',
        on_delete=models.CASCADE,
        blank=True, null=True,
        related_name='versions'
    )
    
    # specified for intellisense, defined in Software model
    software_current: models.Manager['Software']