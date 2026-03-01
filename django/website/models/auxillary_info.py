import uuid
from django.db import models

from ..util import *
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
	access = AccessLevel.PUBLIC
	name = models.CharField(max_length=LEN_NAME)
	identifier = models.CharField(max_length=LEN_NAME, blank=True, null=True)
	funder = models.ForeignKey(
		Organization,
		on_delete=models.SET_NULL,
		blank=True,
		null=True,
		related_name='awards'
	)

	@classmethod
	def get_top_field(cls) -> models.Field: return cls._meta.get_field("name")

	def __str__(self): return self.name
	class Meta: ordering = ['name']

class RelatedItem(ControlledList):
	access = AccessLevel.PUBLIC
	type = models.IntegerField(
		choices=RelatedItemType.choices, 
		default=RelatedItemType.UNKNOWN
	)
	identifier = models.URLField(blank=True, null=True)
	
	# specified for intellisense, defined automatically by django
	get_type_display: Callable[[], str]
	
	def __str__(self): return f"{self.name} ({self.get_type_display()})"
