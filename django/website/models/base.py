"""
Include base models which all models used by HSSI should inherit from, also
pcontains utility types and constants.
"""

import uuid, json
from typing import Any, NamedTuple
from django.db import models
from django.db.models import ManyToManyField, QuerySet
from django.db.models.fields import related_descriptors
from django.core.serializers import serialize

from ..util import *

## Utility Constants & Types ---------------------------------------------------

FIELD_FUNCTIONCATEGORY_FULLNAME = "fullname"
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

## Base Models for HSSI --------------------------------------------------------

class HssiBase(models.base.ModelBase):
	"""
	Used to hook into class generation for models to set name attributes for 
	model fields. Stupid fucking hacky ass way to do it becuase django and 
	python are inflexible. The things I do just to avoid hardcoding strings...
	"""
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
	"""Base class for all models in the HSSI project"""
	access: AccessLevel = AccessLevel.ADMIN
	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

	def get_search_terms(self) -> list[str]: 
		"""
		The search terms that are used for filtering autocomplete suggestions in 
		relevant form interfaces
		"""
		return str(self).split()

	def get_choice(self) -> ModelObjectChoice: 
		return ModelObjectChoice(
			str(self.id), 
			str(self),
			self.get_search_terms(),
			self.get_tooltip(),
		)

	def get_tooltip(self) -> str: return ''
	
	@staticmethod
	def collapse_objects(queryset: QuerySet['HssiModel']) -> 'HssiModel':
		"""
		Useful for if there are multiple entries that should be treated as the 
		same, use this action to collapse all objects to one object, and update
		all references to those objects to point to the new combined object.
		The fields of the combined object will be equal to the first selected 
		object, and appended to if there are any empty fields on that object.
		"""
		print(f"collapsing {queryset.count() - 1} entries in {queryset.model.__name__}..")
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
					print(f"update m2m field {field} with {objvals.count() - ocount} values")
				else:
					objval = getattr(object, field.name)
					if not firstval and objval: 
						setattr(firstobj, field.name, objval)
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

		topfieldname = firstobj._meta.model.get_top_field().name
		print(f"collapsed to '{getattr(firstobj, topfieldname)}:{firstobj.pk}'")
		return firstobj

	@classmethod
	def get_top_field(cls) -> models.Field:
		return None
	
	@classmethod
	def get_second_top_field(cls) -> models.Field:
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
	
	def get_serialized_data(
		self, 
		access: AccessLevel, 
		recursive: bool = False, 
		access_override: AccessLevel = AccessLevel.PUBLIC,
		fields: list[str] = None
	) -> dict[str, Any]:
		"""
		return the instance fields that are available to the specified access 
		level as data in a dictionary. Foreign keys will be fetched and nested 
		in the data structure if 'recursive' is specified.
		"""
		if access < self.access and access_override < self.access:
			raise Exception(f"Unauthorized access, {access} < {self.access}")
		
		datas: str = serialize('json', [self], fields=fields)
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
							new_item = lookup(uuid.UUID(item), self._meta.get_field(key))
							if new_item: new_val.append(new_item)
						except Exception: break
				else:
					try: new_val =  lookup(uuid.UUID(val), self._meta.get_field(key))
					except: continue
				if new_val: data[key] = new_val
		
		# if fields param is specified, remove any non-specified fields
		if fields:
			for key in data:
				if not key in fields: del data[key]

		return data
	
	def to_user_str(self) -> str:
		return str(self)

	class Meta:
		abstract = True

class HssiSet(HssiModel):
	access: AccessLevel = AccessLevel.ADMIN
	target_model: type[HssiModel] = None
	id = models.UUIDField(primary_key=True)

	def get_search_terms(self):
		return self.target_model.objects.get(pk=self.pk).get_search_terms()
	def get_choice(self):
		return self.target_model.objects.get(pk=self.pk).get_choice()
	def get_tooltip(self):
		return self.target_model.objects.get(pk=self.pk).get_tooltip()
	def get_serialized_data(
		self, 
		access, 
		recursive = False, 
		accessOverride = AccessLevel.PUBLIC,
		fields = None,
	):
		if access < self.access and accessOverride < self.access:
			raise Exception(f"Unauthorized access, {access} < {self.access}")
		return self.target_model.objects.get(pk=self.pk).get_serialized_data(
			access, 
			recursive, 
			self.target_model.access,
			fields
		)

	def __str__(self): 
		try:
			software = self.target_model.objects.get(pk=self.id)
			fieldname = self.target_model.get_top_field().name
			return getattr(software, fieldname)
		except:
			return f"<None> - {self.id}"

	class Meta: abstract = True

class ControlledList(HssiModel):
	"""Base class for all controlled lists in the HSSI project"""
	name = models.CharField(max_length=LEN_NAME, blank=False, null=False)
	identifier = models.URLField(blank=True, null=True)
	definition = models.TextField(blank=True, null=True)

	def __str__(self) -> str: return self.name

	@classmethod
	def get_top_field(cls) -> models.Field: return cls._meta.get_field("name")

	def get_tooltip(self): return self.definition

	homepage_filter_field: str | None = None

	def get_homepage_filter_url(self) -> str | None:
		if self.homepage_filter_field is None:
			return None
		from django.urls import reverse
		return (
			reverse("website:published_resources")
			+ "?"
			+ build_software_filter_query(self.homepage_filter_field, self.id)
		)

	def get_search_terms(self) -> list[str]:
		return [
			*self.name
				.replace(',',' ')
				.replace(';',' ')
				.replace(':',' ')
				.split(),
			self.identifier if self.identifier else '',
		]

	@classmethod
	def post_fetch(cls): pass

	class Meta:
		ordering = ['name']
		abstract = True

class ControlledGraphList(ControlledList):
	
	# these are just editor hints, we still need to define child as a 
	# ManyToManyField in any subclasses and set related='parent_nodes'
	children: models.Manager['ControlledGraphList']
	parent_nodes: models.Manager['ControlledGraphList']

	@classmethod
	def apply_old_to_new_mapping(cls, mapping: dict[str, str]):

		# early return if region mapping is already done
		for key, _ in mapping.items():
			try: cls.get_object_with_full_name(key)
			except: 
				print(f"Mapping cancelled: '{key}' not found")
				return

		for old_name, new_name in mapping.items():
			print(f"Apply mapping for {old_name} -> {new_name}...")
			old_match = cls.get_object_with_full_name(old_name)
			new_match = cls.get_object_with_full_name(new_name)
	
			if old_match and new_match:
				replace_database_references(old_match, new_match, False)
	
			else:
				print(cls.objects.first().name)
				raise Exception(
					f"Error mapping old shortlist to rdf graph: " +
					f"{old_match}->{new_match}"
				)
	
			old_match.delete()

		print(f"Old objects mapped to new!")

	@classmethod
	def get_parent_nodes(cls) -> models.QuerySet['ControlledGraphList']:
		""" Returns all objects that have at least one child """
		return cls.objects.filter(children__isnull=False).distinct().order_by("name")
	
	@classmethod
	def get_object_with_full_name(cls, full_name: str) -> 'ControlledGraphList':

		split_name = full_name.split(": ")

		# set root parent to root object with same subname as first 
		# part of fullname
		name_query = cls.objects.filter(name=split_name[0]).filter(parent_nodes__isnull=True)
		parent: 'ControlledGraphList' = name_query.first()

		# go through subnames sequentially finding a match with the same 
		# parent from the previous iteration
		for subname in split_name[1:]:
			name_query = cls.objects.filter(name=subname)
			parent_changed = False
			for obj in name_query:
				if obj.parent_nodes.contains(parent):
					parent = obj
					parent_changed = True
					break
			if not parent_changed:
				raise Exception(
					f"Invalid full name '{full_name}', " +
					f"resolution failed at '{subname}'"
				)
		
		return parent

	def get_full_name(self) -> str:
		""" get a path of all parents recursively pointing to this one """
		path = self.name

		parent = self.parent_nodes.first()
		while parent:
			path = f"{parent.name}: {path}"
			parent = parent.parent_nodes.first()

		return path
	
	def get_serialized_data(
		self, 
		access, 
		recursive = False, 
		access_ovr = AccessLevel.PUBLIC, 
		fields = None
	) -> dict[str, Any]:
		data = super().get_serialized_data(access, recursive, access_ovr, fields)

		if not hasattr(data, "children") and (fields is None or "children" in fields): 
			children: list[uuid.UUID] = []
			for child in self.children.all():
				children.append(child.id)
			data["children"] = children
			
		if not hasattr(data, "parents") and (fields is None or "parents" in fields): 
			parents: list[uuid.UUID] = []
			for parent in self.parent_nodes.all():
				parents.append(parent.id)
			data["parents"] = parents
		
		return data

	class Meta:
		ordering = ['name']
		abstract = True
