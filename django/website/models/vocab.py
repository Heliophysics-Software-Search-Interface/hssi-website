""" Contains controlled metadata models which categorize software entries. """

import colorsys
from django.db import models
from colorful.fields import RGBColorField

from ..util import *
from .base import (
	LEN_NAME, LEN_ABBREVIATION, FIELD_FUNCTIONCATEGORY_FULLNAME,
	ModelObjectChoice, HssiModel, ControlledList, ControlledGraphList
)

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from .software import Software

REGION_MAPPING: dict[str, str] = {
	"Earth Atmosphere": "Magnetosphere: Upper Atmosphere",
	"Interplanetary Space": "Interplanetary space",
	"Planetary Magnetospheres": "Magnetosphere",
	"Earth Magnetosphere": "Magnetosphere",
	"Solar Environment": "Solar Atmosphere"
}

## -----------------------------------------------------------------------------

class InstrObsType(models.IntegerChoices):
	""" Whether an entry in InstrumentObservatory is an instrument or an observatory """
	INSTRUMENT = 1, "Instrument"
	OBSERVATORY = 2, "Observatory"
	UNKNOWN = 3, "Unknown"

## Models ----------------------------------------------------------------------

class Keyword(HssiModel):
	access = AccessLevel.PUBLIC
	name = models.CharField(max_length=LEN_NAME, blank=False, null=False)

	def __str__(self) -> str: return self.name.title()

	@classmethod
	def get_top_field(cls) -> models.Field: return cls._meta.get_field("name")

	class Meta:
		ordering = ['name']

class OperatingSystem(ControlledList):
	"""Operating system on which the software can run"""
	access = AccessLevel.PUBLIC

class CpuArchitecture(ControlledList):
	"""CPU Architecture on which the software can run"""
	access = AccessLevel.PUBLIC
	
class Phenomena(ControlledList):
	"""Solar phenomena that relate to the software"""
	access = AccessLevel.PUBLIC

class RepoStatus(ControlledList):
	"""
	Repo status as defined by the repostatus.org json-ld: 
	https://www.repostatus.org/badges/latest/ontology.jsonld
	"""
	access = AccessLevel.PUBLIC
	image = models.URLField(blank=True, null=True)
	
	class Meta: verbose_name_plural = "Repo Statuses"

class ProgrammingLanguage(ControlledList):
	"""Primary Programming language used to develop the software"""
	access = AccessLevel.PUBLIC
	version = models.CharField(max_length=LEN_NAME, blank=True, null=True)

	def __str__(self): return self.name + (f" {self.version}" if self.version else "")

class DataInput(ControlledList):
	"""Ways that the software can accept data as input"""
	access = AccessLevel.PUBLIC
	abbreviation = models.CharField(max_length=LEN_ABBREVIATION, blank=True, null=True)

	def __str__(self): return self.name

class FileFormat(ControlledList):
	"""File formats that are supported as input or output types by the software"""
	access = AccessLevel.PUBLIC
	extension = models.CharField(max_length=25, blank=False, null=False)

	# specified for intellisense, defined in other models
	softwares_to: models.Manager['Software']
	softwares_from: models.Manager['Software']

	def __str__(self): return self.name + (f" ({self.extension})" if self.extension else "")

class InstrumentObservatory(ControlledList):
	"""An observatory or scientific research instrument"""
	access = AccessLevel.PUBLIC
	type = models.IntegerField(choices=InstrObsType.choices, default=InstrObsType.UNKNOWN)
	abbreviation = models.CharField(max_length=LEN_NAME, null=True, blank=True)

	def get_search_terms(self) -> list[str]:
		terms = super().get_search_terms()
		if self.abbreviation:
			terms.append(self.abbreviation)
		terms.extend(self.name.split(' '))
		return terms
	
	class Meta: ordering = ['name']
	def __str__(self): 
		return f"{self.name} ({self.abbreviation})" if self.abbreviation else self.name

class FunctionCategory(ControlledGraphList):
	access = AccessLevel.PUBLIC
	abbreviation = models.CharField(max_length=5, null=True, blank=True)
	backgroundColor = RGBColorField("Background Color", default="#FFFFFF", blank=True, null=True)
	textColor = RGBColorField("Text Color", default="#000000", blank=True, null=True)

	children = models.ManyToManyField(
		'self',
		blank=True,
		related_name='parent_nodes',
		symmetrical=False,
	)

	# specified for intellisense, defined in other models
	parent_nodes: models.Manager['FunctionCategory']

	def get_choice(self) -> ModelObjectChoice:
		choice_name = str(self)
		if self.parent_nodes:
			if self.parent_nodes.count() == 1:
				choice_name = str(self.parent_nodes.first()) + ": " + choice_name

		return ModelObjectChoice(
			str(self.id), 
			choice_name,
			self.get_search_terms(),
			self.get_tooltip(),
		)

	@classmethod
	def post_fetch(cls):
		super().post_fetch()

		# create appropriate abbreviations for all items
		for obj in cls.objects.all():
			if not obj.abbreviation:
				obj.abbreviation = name_to_abbreviation(obj.name)
				obj.save()

		# get unique colors for each parent
		parents = [x for x in cls.get_parent_nodes()]
		all_objs = []
		delta_hue = 1 / len(parents)
		hue = 0.964 # start at red
		for parent in parents:
			for child in parent.children.all():
				r, g, b = colorsys.hsv_to_rgb(hue, 0.25, 0.9)
				dark = r * 0.299 + g * 0.587 + b * 0.114 <= 0.65
				child.backgroundColor = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}".upper()
				child.textColor = "#FFFFFF" if dark else "#000000"
				if not child in all_objs: all_objs.append(child)
			
			r, g, b = colorsys.hsv_to_rgb(hue, 0.65, 0.9)
			dark = r * 0.299 + g * 0.587 + b * 0.114 <= 0.65
			parent.backgroundColor = f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}".upper()
			parent.textColor = "#FFFFFF" if dark else "#000000"
			all_objs.append(parent)
			hue = (hue + delta_hue) % 1.0
		
		cls.objects.bulk_update(all_objs, ['backgroundColor', 'textColor'])

	def get_search_terms(self):
		arr = super().get_search_terms()
		arr.extend(self.get_full_name().split(": "))
		return arr

	def get_serialized_data(
		self, 
		access, 
		recursive=False, 
		access_ovr=AccessLevel.PUBLIC, 
		fields=None
	):
		include_fullname = (fields and FIELD_FUNCTIONCATEGORY_FULLNAME in fields)
		if include_fullname: 
			fields = list(filter(lambda x: x != FIELD_FUNCTIONCATEGORY_FULLNAME, fields))
		
		data = super().get_serialized_data(access, recursive, access_ovr, fields)
		if include_fullname: 
			data[FIELD_FUNCTIONCATEGORY_FULLNAME] = self.get_full_name()

		return data

	class Meta: verbose_name_plural = "Function Categories"
	def __str__(self): return self.name

class Region(ControlledGraphList):
	"""Region of the sun which relates to the software"""
	access = AccessLevel.PUBLIC
	
	children = models.ManyToManyField(
		'self',
		blank=True,
		related_name='parent_nodes',
		symmetrical=False,
	)

	def get_full_name(self):
		""" get a path of all parents recursively pointing to this one """
		path = self.name

		parent = self.parent_nodes.first()
		if parent: 
			path = path.replace(parent.name, "").strip()
			path = f"{parent.get_full_name()}: {path}"

		return path

	@classmethod
	def post_fetch(cls):
		
		# we don't want no root level single object
		# roots = cls.objects.filter(parent_nodes__isnull=True)
		# for root in roots:
		# 	if root.children.exists():
		# 		print(f"delete root {root.get_full_name()}")
		# 		root.delete()

		cls.apply_old_to_new_mapping(REGION_MAPPING)

	class Meta: ordering = ['name']
	def __str__(self): return self.get_full_name()