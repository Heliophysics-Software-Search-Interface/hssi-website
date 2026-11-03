"""

Module which defines models related to people (authors, users) and their roles.

Covers authors and contacts (`Person`), curators, and submitters. Touch this
when changing how people are stored, displayed, or searched for in forms.
"""

import json
from django.db import models

from ..util import *
from .base import HssiModel, LEN_NAME
from .organizations import Organization

# we need to import the softwares type for intellisense
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from .software import Software, SubmissionInfo

class Person(HssiModel):
	"""Metadata about a person, such as a software author."""
	access = AccessLevel.PUBLIC
	"""Metadata to hold needed information about someone"""
	given_name = models.CharField(max_length=LEN_NAME, null=False, blank=False, default="")
	"""Given (first) name."""
	family_name = models.CharField(max_length=LEN_NAME, null=False, blank=False, default="")
	"""Family (last) name."""
	identifier = models.URLField(blank=True, null=True)
	"""Identifier URL, typically an ORCID."""
	affiliation: Manager[Organization] = models.ManyToManyField(
		Organization, 
		blank=True, 
		related_name='people'
	)
	"""Affiliated `Organization`s."""

	@property
	def fullName(self) -> str:
		"""
		Given and family name joined by a space; setting it splits on the first
		word.
		"""
		return f"{self.given_name} {self.family_name}"

	@fullName.setter
	def fullName(self, value: str):
		self.given_name = value.split()[0]
		self.family_name = value.removeprefix(self.given_name).strip()

	# specified for intellisense, defined in other models
	softwares: models.Manager['Software']
	"""Reverse relation to `Software` entries."""
	submission_info: models.Manager['SubmissionInfo']
	"""Reverse relation to `SubmissionInfo` entries."""
	curator: models.Manager['Curator']
	"""Reverse relation to the person's `Curator` row."""

	@staticmethod
	def get_default_person() -> 'Person':
		"""The placeholder "UNKNOWN" person, created if it doesn't exist."""
		pers = Person.objects.filter(given_name="UNKNOWN").first()
		if not pers:
			pers = Person()
			pers.given_name = "UNKNOWN"
			pers.family_name = "UNKNOWN"
			pers.save()
		return pers

	def get_search_terms(self) -> list[str]:
		"""
		Meta info that allows data in this model to be serialized to allow for
		user discovery.
		"""
		terms = super().get_search_terms()
		if self.identifier:
			terms.append(self.identifier)
			terms.append(str.split(self.identifier, "orcid.org/")[-1])
		return terms

	@classmethod
	def get_top_field(cls) -> models.Field:
		"""Returns the `given_name` field as the model's display field."""
		return cls._meta.get_field("given_name")
	@classmethod
	def get_second_top_field(cls) -> models.Field:
		"""
		Returns the `family_name` field as the model's secondary display field.
		"""
		return cls._meta.get_field("family_name")

	class Meta: 
		ordering = ['family_name', 'given_name']
		verbose_name_plural = 'People'
	def __str__(self): 
		name = self.given_name + " " + self.family_name
		if self.identifier:
			name += f" ({str.split(self.identifier, "orcid.org/")[-1]})"
		return name

	def to_str_lastname_firstname(self) -> str:
		"""
		The name as `"Family, Given"`, or just the given name if there is no
		family name.
		"""
		if self.family_name is None or len(self.family_name) <= 0:
			return self.given_name
		return f"{self.family_name}, {self.given_name}"

class Curator(HssiModel):
	"""A user who is able to curate submissions."""
	access = AccessLevel.CURATOR
	"""A user who is able to curate submissions"""
	email = models.EmailField(null=False, blank=False)
	"""Curator's email address."""
	person = models.OneToOneField(
			Person, 
			on_delete=models.SET_DEFAULT, 
			default=Person.get_default_person,
			null=False, blank=False, 
			related_name='curator'
		)
	"""The curator's `Person`; defaults to the placeholder "UNKNOWN" person."""

	# specified for intellisense, defined in other models
	submission_infos: models.Manager['SubmissionInfo']
	"""
	Reverse relation to `SubmissionInfo` entries the curator is assigned to.
	"""
	submission_infos_led: models.Manager['SubmissionInfo']
	"""Reverse relation to `SubmissionInfo` entries the curator leads."""

	@classmethod
	def get_top_field(cls) -> models.Field:
		"""Returns the `email` field as the model's display field."""
		return cls._meta.get_field("email")

	class Meta: ordering = ['person']
	def __str__(self): return str(self.person)

class Submitter(HssiModel):
	"""A person who has submitted a software."""
	access = AccessLevel.CURATOR
	"""A person who has submitted a software"""
	email = models.EmailField(null=False, blank=False)
	"""Submitter's email address, or a JSON-style list of addresses."""
	person = models.ForeignKey(
			Person, 
			on_delete=models.SET_DEFAULT,
			default=Person.get_default_person,
			null=False, blank=False, 
			related_name='submitter'
		)
	"""
	The submitter's `Person`; defaults to the placeholder "UNKNOWN" person.
	"""

	# specified for intellisense, defined in other models
	submission_infos: models.Manager['SubmissionInfo']
	"""Reverse relation to `SubmissionInfo` entries."""

	@property
	def fullName(self) -> str:
		"""The linked person's full name."""
		return self.person.fullName

	def email_list(self) -> list[str]:
		"""
		The `email` field parsed as a list of addresses, or a single-item list
		if it isn't a list.
		"""
		if not self.email: return []
		jsonstr: str = self.email
		jsonstr = jsonstr.replace("'", '"')
		emails = []
		try: 
			emails = json.loads(jsonstr)
			assert isinstance(emails, list)
		except:
			return [self.email]
		return emails

	@staticmethod
	def get_default_submitter() -> 'Submitter':
		"""
		The placeholder submitter with email "UNKNOWN"; a newly created one is
		not saved.
		"""
		sub = Submitter.objects.filter(email="UNKNOWN").first()
		if not sub:
			sub = Submitter()
			sub.email="UNKNOWN"
			sub.save
		return sub

	@classmethod
	def get_top_field(cls) -> models.Field:
		"""Returns the `email` field as the model's display field."""
		return cls._meta.get_field("email")
	
	class Meta: ordering = ['person']
	def __str__(self): return str(self.person)
