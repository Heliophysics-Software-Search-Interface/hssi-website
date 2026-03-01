""" 
TODO 
"""

from typing import Callable
from django.db import models

from ..util import *
from .base import ControlledList

class RelatedItemType(models.IntegerChoices):
	'''The type of an object in the RelatedField model'''
	SOFTWARE = 1, "Software"
	DATASET = 2, "Dataset"
	PUBLICATION = 3, "Publication"
	UNKNOWN = 4, "Unknown"

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