""" Module for Organization and Award models """

from django.db import models

from ..util import *
from .base import LEN_NAME, LEN_SHORTNAME, HssiModel

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from .people import Person
	from .software import Software

class Organization(HssiModel):
	"""A legal entity such as university, agency, or company"""
	access = AccessLevel.PUBLIC
	name = models.CharField(max_length=LEN_NAME)
	abbreviation = models.CharField(max_length=LEN_SHORTNAME, null=True, blank=True)
	website = models.URLField(blank=True, null=True)
	identifier = models.URLField(blank=True, null=True)

	# specified for intellisense, defined in other models
	people: models.Manager['Person']
	awards: models.Manager['Award']
	softwares_published: models.Manager['Software']
	softwares_funded: models.Manager['Software']

	@classmethod
	def get_top_field(cls) -> models.Field: return cls._meta.get_field("name")

	def get_search_terms(self) -> list[str]:
		terms = self.name.split()
		if self.abbreviation:
			terms.append(self.abbreviation)
		if self.identifier:
			terms.append(self.identifier)
			terms.append(str.split(self.identifier, "ror.org/")[-1])
		return terms

	class Meta: ordering = ['name']
	def __str__(self):
		if self.abbreviation:
			return f"{self.name} ({self.abbreviation})"
		return self.name

class Award(HssiModel):
	"""A grant or other funding award given by an organization"""
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