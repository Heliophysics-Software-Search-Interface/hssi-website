import json
from django.db import models

from ..util import *
from .roots import HssiModel, Organization, LEN_NAME

from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from .auxillary_info import RelatedItem

# we need to import the softwares type for intellisense
from typing import TYPE_CHECKING
if TYPE_CHECKING:
	from .software import Software
	from .submission_info import SubmissionInfo

class Person(HssiModel):
	access = AccessLevel.PUBLIC
	'''Metadata to hold needed information about someone'''
	given_name = models.CharField(max_length=LEN_NAME, null=False, blank=False, default="")
	family_name = models.CharField(max_length=LEN_NAME, null=False, blank=False, default="")
	identifier = models.URLField(blank=True, null=True)
	affiliation = models.ManyToManyField(
		Organization, 
		blank=True, 
		related_name='people'
	)

	@property
	def fullName(self) -> str:
		return f"{self.given_name} {self.family_name}"

	@fullName.setter
	def fullName(self, value: str):
		self.given_name = value.split()[0]
		self.family_name = value.removeprefix(self.given_name).strip()

	# specified for intellisense, defined in other models
	softwares: models.Manager['Software']
	submission_info: models.Manager['SubmissionInfo']
	curator: models.Manager['Curator']

	@staticmethod
	def get_default_person() -> 'Person':
		pers = Person.objects.filter(firstName="UNKNOWN").first()
		if not pers:
			pers = Person()
			pers.given_name = "UNKNOWN"
			pers.family_name = "UNKNOWN"
			pers.save()
		return pers

	# meta info that allows data in this model to be serialized to allow for user discovery
	def get_search_terms(self) -> list[str]:
		terms = super().get_search_terms()
		if self.identifier:
			terms.append(self.identifier)
			terms.append(str.split(self.identifier, "orcid.org/")[-1])
		return terms

	@classmethod
	def get_top_field(cls) -> models.Field: return cls._meta.get_field("given_name")
	@classmethod
	def get_second_top_field(cls) -> models.Field: return cls._meta.get_field("family_name")

	class Meta: 
		ordering = ['family_name', 'given_name']
		verbose_name_plural = 'People'
	def __str__(self): 
		name = self.given_name + " " + self.family_name
		if self.identifier:
			name += f" ({str.split(self.identifier, "orcid.org/")[-1]})"
		return name

	def to_str_lastname_firstname(self) -> str:
		if self.family_name is None or len(self.family_name) <= 0:
			return self.given_name
		return f"{self.family_name}, {self.given_name}"

class Curator(HssiModel):
	access = AccessLevel.CURATOR
	'''A user who is able to curate submissions'''
	email = models.EmailField(null=False, blank=False)
	person = models.OneToOneField(
			Person, 
			on_delete=models.SET_DEFAULT, 
			default=Person.get_default_person,
			null=False, blank=False, 
			related_name='curator'
		)

	# specified for intellisense, defined in other models
	submission_infos: models.Manager['SubmissionInfo']
	submission_infos_led: models.Manager['SubmissionInfo']

	@classmethod
	def get_top_field(cls) -> models.Field: return cls._meta.get_field("email")

	class Meta: ordering = ['person']
	def __str__(self): return str(self.person)

class Submitter(HssiModel):
	access = AccessLevel.CURATOR
	'''A person who has submitted a software'''
	email = models.EmailField(null=False, blank=False)
	person = models.ForeignKey(
			Person, 
			on_delete=models.SET_DEFAULT,
			default=Person.get_default_person,
			null=False, blank=False, 
			related_name='submitter'
		)

	# specified for intellisense, defined in other models
	submission_infos: models.Manager['SubmissionInfo']

	@property
	def fullName(self) -> str:
		return self.person.fullName

	def email_list(self) -> list[str]:
		if not self.email: return []
		jsonstr: str = self.email
		jsonstr = jsonstr.replace("'", '"')
		return json.loads(jsonstr)

	@staticmethod
	def get_default_submitter() -> 'Submitter':
		sub = Submitter.objects.filter(email="UNKNOWN").first()
		if not sub:
			sub = Submitter()
			sub.email="UNKNOWN"
			sub.save
		return sub

	@classmethod
	def get_top_field(cls) -> models.Field: return cls._meta.get_field("email")
	
	class Meta: ordering = ['person']
	def __str__(self): return str(self.person)
