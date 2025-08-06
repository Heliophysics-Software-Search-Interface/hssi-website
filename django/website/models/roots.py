import uuid, json
from django.db import models
from django.db.models import ManyToManyField, QuerySet
from django.db.models.fields import related_descriptors
from django.core.serializers import serialize
from colorful.fields import RGBColorField

from .structurizer import form_config
from ..util import *

from typing import TYPE_CHECKING, Any, NamedTuple
if TYPE_CHECKING:
	from .people import Person
	from .auxillary_info import Award, RelatedItem
	from .software import Software

FIELD_HAS_FOREIGN_KEY = (
	models.ForeignKey | models.ManyToManyField | models.OneToOneField
)

# Character length limits
LEN_LONGNAME = 512
LEN_NAME = 128
LEN_SHORTNAME = 16
LEN_ABBREVIATION = 5

class ModelObjectChoice(NamedTuple):
	id: str
	name: str
	keywords: list[str]
	tooltip: str

# Whether an entry in InstrumentObservatory is an instrument or an observatory
class InstrObsType(models.IntegerChoices):
	INSTRUMENT = 1, "Instrument"
	OBSERVATORY = 2, "Observatory"
	UNKNOWN = 3, "Unknown"

class HssiBase(models.base.ModelBase):
	'''
	Used to hook into class generation for models to set name attributes for 
	model fields. Stupid fucking hacky ass way to do it becuase django and 
	python are inflexible. The things I do just to avoid hardcoding strings...
	'''
	def __new__(cls: type['HssiModel'], name, bases, attrs: dict[str, Any], **kwargs):
		new_cls = super().__new__(cls, name, bases, attrs, **kwargs)
		for key, val in new_cls.__dict__.items():
			if (
				isinstance(val, models.query_utils.DeferredAttribute) or 
				isinstance(val, related_descriptors.ForwardOneToOneDescriptor) or 
				isinstance(val, related_descriptors.ForwardManyToOneDescriptor)
			):
				setattr(val, "name", key)
		return new_cls

class HssiModel(models.Model, metaclass=HssiBase):
	'''Base class for all models in the HSSI project'''
	access: AccessLevel = AccessLevel.ADMIN
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	def get_search_terms(self) -> list[str]: 
		'''
		The search terms that are used for filtering autocomplete suggestions in 
		relevant form interfaces
		'''
		return str(self).split()

	def get_choice(self) -> ModelObjectChoice: 
		return ModelObjectChoice(
			str(self.id), 
			str(self),
			self.get_search_terms(),
			self.get_tooltip(),
		)

	def get_tooltip(self) -> str: return ''

	def __init_subclass__(cls) -> None:
		cls._form_config_redef()
		return super().__init_subclass__()
	
	@staticmethod
	def collapse_objects(queryset: QuerySet['HssiModel']) -> 'HssiModel':
		"""
		Useful for if there are multiple entries that should be treated as the 
		same, use this action to collapse all objects to one object, and update
		all references to those objects to point to the new combined object.
		The fields of the combined object will be equal to the first selected 
		object, and appended to if there are any empty fields on that object.
		"""
		print(f"collapsing {queryset.count() - 1} entries in {queryset.model.name}..")
		firstobj: HssiModel = None
		for object in queryset:
			if firstobj is None:
				firstobj = object
				continue

			# concatenate all fields, if first object has an empty field, fill
			# it with the value from a collapsed object, or if it is missing
			# entries in a m2m field, add them
			for field in object._meta.get_fields():
				if field.is_relation and field.auto_created and not field.concrete: continue
				firstval = getattr(firstobj, field.name)
				if isinstance(field, ManyToManyField):
					objvals: models.Manager = getattr(object, field.name)
					ocount = objvals.count()
					for val in objvals.all(): firstval.add(val)
					print(f"update m2m field {field} with {objvals.count - ocount} values")
				else:
					objval = getattr(object, field.name)
					if not firstval and objval: 
						setattr(firstval, field.name, objval)
						print(f"update field {field} to '{objval}'")
			
			refs = find_database_references(object)
			for refobj, field in refs:

				# many to many fields need to be handled separately since they
				# hold multiple foreign key references instead of just one
				if isinstance(field, ManyToManyField): 
					manager = getattr(refobj, field.name)
					manager.remove(object)
					manager.add(firstobj)
				else: setattr(refobj, field.name, firstobj)
				refobj.save()
				print(f"updated '{refobj}:{field}' field")

			firstobj.save()
			object.delete()

		print(f"collapsed to '{firstobj.name}'")
		return firstobj

	@classmethod
	def _form_config_redef(cls) -> None:
		'''Redefine the form properties for fields here'''
		pass

	@classmethod
	def get_top_field(cls) -> models.Field:
		return None
	
	@classmethod
	def get_subfields(cls) -> list[models.Field]:
		subfields = []

		# get top field since we want to skip it
		top_field = cls.get_top_field()

		# iterate through each field and create subfield structures for concrete model fields
		fields = cls._meta.get_fields(include_parents=True, include_hidden=False)
		for field in fields:

			# we don't want reverse or non-column fields (or the top field)
			if field == top_field or field.auto_created or not field.concrete or not field.editable:
				continue
			subfields.append(field)
		
		return subfields
	
	def get_serialized_data(self, access: AccessLevel, recursive: bool = False) -> dict[str, Any]:
		"""
		return the instance fields that are available to the specified access 
		level as data in a dictionary. Foreign keys will be fetched and nested 
		in the data structure if 'recursive' is specified
		"""
		model = type(self)
		if access < model.access:
			raise Exception(f"Unauthorized access, {access} < {model.access}")
		
		datas: str = serialize('json', [self])
		data: dict[str, Any] = json.loads(datas)[0].get('fields')
		data['id'] = str(self.id)

		# TODO handle potential infinite recursion for circular table references
		if recursive:
			def lookup(uid: str, field: FIELD_HAS_FOREIGN_KEY) -> dict[str, Any] | None | str:
				if isinstance(field, FIELD_HAS_FOREIGN_KEY):
					target_model: type[HssiModel] = field.related_model
					if not issubclass(target_model, HssiModel): return None
					instance = target_model.objects.filter(pk=uid).first()
					parsed_val: dict[str, Any] = None
					try: parsed_val = instance.get_serialized_data(access, recursive)
					except Exception: return "ERROR"
					return parsed_val
				return None
			
			for key, val in data.items():
				if key == 'id': continue
				if isinstance(val, list):
					new_val: list = []
					for item in val:
						if not item: continue
						try:
							new_item = lookup(uuid.UUID(item), model._meta.get_field(key))
							if new_item: new_val.append(new_item)
						except Exception: break
					if new_val: data[key] = new_val
					continue
				try:
					new_val =  lookup(uuid.UUID(val), model._meta.get_field(key))
					if new_val: data[key] = new_val
				except: continue
		return data
	
	class Meta:
		abstract = True

class ControlledList(HssiModel):
	'''Base class for all controlled lists in the HSSI project'''
	name = form_config(
		models.CharField(max_length=LEN_NAME, blank=False, null=False),
		# widgetType="ModelBox",
		label="Name",
		widgetProperties={
			'requirementLevel': RequirementLevel.MANDATORY.value,
		},
	)

	identifier = form_config(
		models.URLField(blank=True, null=True),
		label="Identifier",
	)

	definition = form_config(
		models.TextField(blank=True, null=True),
		label="Definition",
	)

	def __str__(self) -> str: return self.name

	@classmethod
	def get_top_field(cls) -> models.Field: return cls._meta.get_field("name")

	def get_tooltip(self): return self.definition

	def get_search_terms(self) -> list[str]:
		return [
			*self.name
				.replace(',',' ')
				.replace(';',' ')
				.replace(':',' ')
				.split(), 
			self.identifier if self.identifier else '',
		]

	class Meta:
		ordering = ['name']
		abstract = True

class ControlledGraphList(ControlledList):
	
	# these are just editor hints, we still need to define child as a 
	# ManyToManyField in any subclasses and set related='parent_nodes'
	children: models.Manager['ControlledGraphList']
	parent_nodes: models.Manager['ControlledGraphList']

	@classmethod
	def get_parent_nodes(cls) -> models.QuerySet['ControlledGraphList']:
		''' Returns all objects that have at least one child '''
		return cls.objects.filter(children__isnull=False).distinct()

	class Meta:
		ordering = ['name']
		abstract = True

## Simple Root Models ----------------------------------------------------------

class Keyword(ControlledList):
	access = AccessLevel.PUBLIC
	@classmethod
	def _form_config_redef(cls) -> None:
		super()._form_config_redef()
		form_config(
			cls._meta.get_field(cls.name.name),
			label="Keyword",
			tooltipExplanation="General science keywords relevant for the software (e.g. from the AGU Index List of the UAT) not supported by other metadata fields.",
			tooltipBestPractise="Begin typing the keyword in the box. Keywords listed in the UAT and AGU Index lists will appear in a dropdown list, please choose the correct one(s). If your keyword is not listed, please type it in.",
		)

	def __str__(self) -> str: return self.name.title()

class OperatingSystem(ControlledList):
	'''Operating system on which the software can run'''
	access = AccessLevel.PUBLIC
	@classmethod
	def _form_config_redef(cls) -> None:
		super()._form_config_redef()
		form_config(
			cls._meta.get_field(cls.name.name),
			label="Operating System",
			tooltipExplanation="The operating systems the software supports.",
			tooltipBestPractise="Please select all the operating systems the software can successfully be installed on.",
		)

class CpuArchitecture(ControlledList):
	'''CPU Architecture on which the software can run'''
	access = AccessLevel.PUBLIC
	@classmethod
	def _form_config_redef(cls) -> None:
		super()._form_config_redef()
		form_config(
			cls._meta.get_field(cls.name.name),
			label="CPU Architecture",
			tooltipExplanation="",
			tooltipBestPractise="",
		)

class Phenomena(ControlledList):
	'''Solar phenomena that relate to the software'''
	access = AccessLevel.PUBLIC
	@classmethod
	def _form_config_redef(cls) -> None:
		super()._form_config_redef()
		form_config(
			cls._meta.get_field(cls.name.name),
			label="Related Phenomena",
			tooltipExplanation="The phenomena the software supports science functionality for.",
			tooltipBestPractise="Please select phenomena terms from a supported controlled vocabulary.",
		)

class RepoStatus(ControlledList):
	'''
	Repo status as defined by the repostatus.org json-ld: 
	https://www.repostatus.org/badges/latest/ontology.jsonld
	'''
	access = AccessLevel.PUBLIC
	image = models.URLField(blank=True, null=True)

	@classmethod
	def _form_config_redef(cls) -> None:
		super()._form_config_redef()
		form_config(
			cls._meta.get_field(cls.name.name),
			label="Development Status",
			tooltipExplanation="The development status of the software.",
			tooltipBestPractise="Please select the development status of the code repository from the list below. See repostatus.org for a description of the terms.",
		)
	
	class Meta: verbose_name_plural = "Repo Statuses"

class Image(HssiModel):
	'''Reference to an image file and alt text description'''
	access = AccessLevel.PUBLIC
	url = models.URLField(blank=True, null=True)
	description = models.CharField(max_length=250)

	@classmethod
	def get_top_field(cls): return cls._meta.get_field("url")

	class Meta: ordering = ['description']
	def __str__(self): return self.url

class ProgrammingLanguage(ControlledList):
	'''Primary Programming language used to develop the software'''
	access = AccessLevel.PUBLIC
	version = models.CharField(max_length=LEN_NAME, blank=True, null=True)

	@classmethod
	def _form_config_redef(cls) -> None:
		super()._form_config_redef()
		form_config(
			cls._meta.get_field(cls.name.name),
			label="Programming Language",
			tooltipExplanation="The computer programming languages most important for the software.",
			tooltipBestPractise="Select the most important languages of the software (e.g. Python, Fortran, C), then enter any other needed details, e.g. the flavor of Fortran. This is not meant to be an exhaustive list.",
		)

	def __str__(self): return self.name + (f" {self.version}" if self.version else "")

class DataInput(ControlledList):
	'''Ways that the software can accept data as input'''
	access = AccessLevel.PUBLIC
	abbreviation = models.CharField(max_length=LEN_ABBREVIATION, blank=True, null=True)

	@classmethod
	def _form_config_redef(cls) -> None:
		super()._form_config_redef()
		form_config(
			cls._meta.get_field(cls.name.name),
			label="Data Inputs",
			tooltipExplanation="The data input source the software supports.",
			tooltipBestPractise="Please select all the data input sources the software supports from the list. If a data input source your software supports is not listed, please select 'Other'. If the data input source is observatory specific, please select 'observatory-specific' and make sure to indicate the name of the observatory, mission, or group of instruments in the Related Observatory field.",
		)

	def __str__(self): return self.name

class FileFormat(ControlledList):
	'''File formats that are supported as input or output types by the software'''
	access = AccessLevel.PUBLIC
	extension = models.CharField(max_length=25, blank=False, null=False)

	# specified for intellisense, defined in other models
	softwares_to: models.Manager['Software']
	softwares_from: models.Manager['Software']

	@classmethod
	def _form_config_redef(cls) -> None:
		super()._form_config_redef()
		form_config(
			cls._meta.get_field(cls.name.name),
			label="File Formats",
			tooltipExplanation="The file formats the software supports for data input or output.",
			tooltipBestPractise="Please select all the file formats that your software supports for either input files or files the software generates. Only file formats supported by the software should be indicated.",
		)

	def __str__(self): return self.name + (f" ({self.extension})" if self.extension else "")

class Region(ControlledList):
	'''Region of the sun which relates to the software'''
	access = AccessLevel.PUBLIC
	@classmethod
	def _form_config_redef(cls) -> None:
		super()._form_config_redef()
		form_config(
			cls._meta.get_field(cls.name.name),
			label="Related Regions",
			tooltipExplanation="The physical region the software supports science functionality for.",
			tooltipBestPractise="Please select all physical regions the software's functionality is commonly used or intended for.",
		)
	
	class Meta: ordering = ['name']
	def __str__(self): return self.name

class InstrumentObservatory(ControlledList):
	'''An observatory or scientific research instrument'''
	access = AccessLevel.PUBLIC
	type = form_config(
		models.IntegerField(choices=InstrObsType.choices, default=InstrObsType.UNKNOWN),
		label="Type",
		widgetType="NumberWidget",
	)
	
	abbreviation = form_config(
		models.CharField(max_length=LEN_NAME, null=True, blank=True),
		label="Abbreviation",
	)

	@classmethod
	def _form_config_redef(cls) -> None:
		super()._form_config_redef()
		form_config(
			cls._meta.get_field(cls.name.name),
			label="Instrument/Observatory",
			tooltipExplanation="The instrument/observatory the software is designed to support.",
			tooltipBestPractise="Begin typing the item's name in the box. Instruments/Observatories listed in the IVOA will appear in a dropdown list, please choose the correct one. If your instrument/observatory is not listed, please type in the full name.",
		)

	def get_search_terms(self) -> list[str]:
		terms = super().get_search_terms()
		if self.abbreviation:
			terms.append(self.abbreviation)
		terms.extend(self.name.split(' '))
		return terms
	
	class Meta: ordering = ['name']
	def __str__(self): 
		return f"{self.name} ({self.abbreviation})" if self.abbreviation else self.name

## Complex Root Models ---------------------------------------------------------

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
	def _form_config_redef(cls) -> None:
		super()._form_config_redef()
		form_config(
			cls._meta.get_field(cls.name.name),
			label="Functionality",
			tooltipExplanation="A category that contains functionalities.",
		)

	class Meta: verbose_name_plural = "Function Categories"
	def __str__(self): return self.name

class License(HssiModel):
	access = AccessLevel.PUBLIC
	name = models.CharField(max_length=LEN_NAME)
	url = models.URLField(blank=True, null=True)

	# specified for intellisense, defined in other models
	relatedItems: models.Manager['RelatedItem']

	@classmethod
	def get_top_field(cls): return cls._meta.get_field("name")

	def get_search_terms(self):
		terms = super().get_search_terms()
		if self.url:
			terms.append(self.url)
		return terms
	
	class Meta: ordering = ['name']
	def __str__(self): return self.name

class Organization(HssiModel):
	'''A legal entity such as university, agency, or company'''
	access = AccessLevel.PUBLIC
	name = models.CharField(max_length=LEN_NAME)
	abbreviation = models.CharField(max_length=LEN_SHORTNAME, null=True, blank=True)
	website = models.URLField(blank=True, null=True)
	identifier = models.URLField(blank=True, null=True)
	parent_organization = models.ForeignKey(
		'self', 
		on_delete=models.CASCADE, 
		null=True, 
		blank=True, 
		related_name='sub_organizations'
	)

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
