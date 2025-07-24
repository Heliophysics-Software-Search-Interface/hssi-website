import uuid
from django.db import models

from .structurizer import form_config
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
	name = form_config(
		models.CharField(max_length=LEN_NAME),
		label="Award",
		tooltipExplanation="The title of the specific grant or award that funded the work.",
		tooltipeBestPractise="Please copy the full title of the award here.",
	)

	identifier = form_config(
		models.CharField(max_length=LEN_NAME, blank=True, null=True),
		label="Award Number",
		tooltipExplanation="The award number or other identifier associated with the award.",
		tooltipBestPractise="Please copy the identifier associated with the award here, e.g. NNG19PQ28C. This is used by funding agencies and organizations to track the impact of their funding.",
	)

	funder = form_config(
		models.ForeignKey(
			Organization,
			on_delete=models.CASCADE,
			blank=True,
			null=True,
			related_name='awards'
		),
		label="Funder",
		tooltipExplanation="A person or organization that supports (sponsors) something through some kind of financial contribution.",
		tooltipBestPractise="The name of the organization that provided the funding, e.g. NASA or The Sloan Foundation.",
	)

	@classmethod
	def get_top_field(cls) -> models.Field: return cls._meta.get_field("name")

	class Meta: ordering = ['name']
	def __str__(self): return self.name

class RelatedItem(ControlledList):
	type = form_config(
		models.IntegerField(
			choices=RelatedItemType.choices, 
			default=RelatedItemType.UNKNOWN
		),
		widgetType="NumberWidget",
	) 
	identifier = form_config(
		models.URLField(blank=True, null=True),
		label="Identifier",
		tooltipExplanation="The identifier for the item (e.g. the DOI).",
	) 
	authors = form_config(
		models.ManyToManyField(
			Person,
			blank=True,
			related_name='relatedItems'
		),
		label="Authors",
		tooltipExplanation="The authors of this item.",
	) 
	creditText = form_config(
		models.TextField(blank=True, null=True),
		label="Credit Text",
		tooltipExplanation="",
		tooltipBestPractise="",
	) 
	license = form_config(
		models.ForeignKey(
			License,
			on_delete=models.CASCADE,
			blank=True, null=True,
			related_name='relatedItems'
		),
		label="License",
		tooltipExplanation="The license assigned to the item (e.g. Creative Commons Zero v1.0 Universal). Licenses supported by SPDX are preferred. See https://spdx.org/licenses/ for details.",
		tooltipBestPractise="Please enter the complete license and include version information if applicable.",
	) 

	@classmethod
	def _form_config_redef(cls) -> None:
		super()._form_config_redef()
		form_config(
			cls._meta.get_field(cls.name.name),
			label="Related Item",
			tooltipExplanation="An item related to the software in some way.",
		)
	
	# specified for intellisense, defined automatically by django
	get_type_display: Callable[[], str]
	
	def __str__(self): return f"{self.name} ({self.get_type_display()})"