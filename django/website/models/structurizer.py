"""
This module handles translating the django model structure into serializable
data structures that can be passed to the website frontend modules in
/frontend/forms and be used to generate forms on the clientside that represent
the exposed django model structure
"""

import json
import warnings

from django.db import models
from django.db.models.manager import BaseManager
from django.db.models.fields import related
from django.forms import widgets

from ..util import RequirementLevel, AccessLevel, REQ_LVL_ATTR

from enum import StrEnum
from typing import Type, TYPE_CHECKING, Any
if TYPE_CHECKING:
	from .roots import HssiModel

FORM_CONFIG_ATTR = "form_config"

registered_structures: dict[str, 'ModelStructure'] = {}

def register_structure(*structure: 'ModelStructure'):
	for struct in structure: registered_structures[struct.type_name] = struct

def form_config(field: models.Field, **kwargs) -> models.Field:
	'''
	Allows for configuration of field properties to pass as model field 
	structure to frontend for form generation
	'''
	config = getattr(field, FORM_CONFIG_ATTR, {})
	setattr(field, FORM_CONFIG_ATTR, config | kwargs)
	return field

class WidgetPrimitiveName(StrEnum):
	char = "CharWidget"
	number = "NumberWidget"
	textArea = "TextAreaWidget"
	url = "UrlWidget"
	email = "EmailWidget"
	date = "DateWidget"
	checkbox = "CheckboxWidget"

class ModelSubfield:
	"""
	TODO
	"""

	name: str = ""
	row_name: str = ""
	type: str = ""
	requirement: RequirementLevel = RequirementLevel.OPTIONAL.value
	properties: dict = {}
	multi: bool = False

	def serialized(self) -> dict:
		"""
		return a serializeable dictionary representation of the data that this 
		model subfield holds
		"""
		return {
			'name': self.name,
			'rowName': self.row_name,
			'type': self.type,
			'requirement': self.requirement,
			'properties': self.properties,
			'multi': self.multi,
		}
	
	def to_json(self) -> str:
		return json.dumps(self.serialized)

	@classmethod
	def create(cls, field: models.Field) -> 'ModelSubfield':
		""" create a subfield based on a model field """

		if field is None: return None

		subfield = cls()
		subfield.name = field.name
		subfield.row_name = field.name

		# get custom widget properties if defined
		properties: dict = getattr(field, FORM_CONFIG_ATTR, {})
		
		if isinstance(field, related.RelatedField):
			subfield.multi = isinstance(field, related.ManyToManyField)
			subfield.type = properties.get('widgetType', field.related_model.__name__)

		else:
			widget: widgets.Widget = field.formfield().widget
			properties = widget.attrs | properties
			subfield.requirement = RequirementLevel(
				properties.get(REQ_LVL_ATTR, RequirementLevel.OPTIONAL.value)
			)
			widgetType = properties.get('widgetType', None)
			if widgetType is not None:
				subfield.type = widgetType
			else: 
				match widget:
					case widgets.TextInput(): subfield.type = WidgetPrimitiveName.char.value 
					case widgets.NumberInput(): subfield.type = WidgetPrimitiveName.number.value
					case widgets.Textarea(): subfield.type = WidgetPrimitiveName.textArea.value
					case widgets.URLInput(): subfield.type = WidgetPrimitiveName.url.value
					case widgets.EmailInput(): subfield.type = WidgetPrimitiveName.email.value
					case widgets.DateInput(): subfield.type = WidgetPrimitiveName.date.value
					case widgets.CheckboxInput(): subfield.type = WidgetPrimitiveName.checkbox.value
		
		subfield.properties = properties
		return subfield

	@classmethod
	def define(
		cls, name: str, type: str, requirement: int, properties: dict, multi: bool, 
		row_name: str = ""
	) -> 'ModelSubfield':

		sf = ModelSubfield()
		sf.name = name
		sf.row_name = row_name
		sf.type = type
		sf.requirement = requirement
		sf.properties = properties
		sf.multi = multi
		return sf

class ModelStructure:
	"""
	TODO
	"""

	target_model: type['HssiModel'] = None
	type_name: str = ""
	top_field: ModelSubfield | None = None
	subfields: list[ModelSubfield] = []

	@classmethod
	def create(cls, model: Type['HssiModel']) -> 'ModelStructure':
		""" create a model structure based on the given hssi model class """

		structure = ModelStructure()
		structure.target_model = model
		structure.type_name = model.__name__
		structure.top_field = ModelSubfield.create(model.get_top_field())
		structure.subfields = [
			ModelSubfield.create(subfield)
			for subfield in model.get_subfields()
		] 

		return structure
	
	@classmethod
	def define(cls, 
		target_model: type['HssiModel'],  
		name: str, 
		*fields: ModelSubfield
	) -> 'ModelStructure':

		fields_list = list(fields)

		structure = cls()
		structure.target_model = target_model
		structure.type_name = name
		structure.top_field = fields_list.pop(0)
		structure.subfields = fields_list

		return structure

	def split(self, field_name: str, name_left: str, name_right: str) -> list['ModelStructure']:
		"""
		split the field structure into two, starting at the field with 
		the specified name
		"""
		for i, field in enumerate(self.subfields):
			if field.name == field_name:
				structure1 = ModelStructure.define(
					self.target_model,
					name_left,
					self.top_field,
					*self.subfields[0:i],
				)
				structure2 = ModelStructure.define(
					self.target_model,
					name_right,
					*self.subfields[i:],
				)
				return [structure1, structure2]

		return [self]

	def serialize_model_object(
		self, 
		object: 'HssiModel', 
		recursive: bool,
		access: AccessLevel = AccessLevel.PUBLIC,
	) -> dict[str, Any]:
		"""
		force an object to conform to this specific model structure.
		creates a JSON serializable dict from the object data, but only with 
		the values from fields specified in this structure, replacing the 
		field names as defined
		"""
		if access < self.target_model.access:
			raise Exception(f"Unauthorized access, {access} < {self.target_model.access}")
		
		if not issubclass(object._meta.model, self.target_model): 
			raise Exception(
				f"incompatible model types '{object._meta.model}', '{self.target_model}'"
			)
		
		data: dict[str, Any] = {}
		for mfield in self:
			fname = mfield.name
			val: Any = None
			if hasattr(object, mfield.name): val = getattr(object, mfield.name)
			elif hasattr(object, mfield.row_name): val = getattr(object, mfield.row_name)
			if not val: 
				print(f"field [{fname}|{mfield.row_name}] not found on {object}")
				continue
			# TODO handle potential infinite recursion for circular table references
			if recursive and (isinstance(val, models.Model) or isinstance(val, BaseManager)):
				struct = registered_structures.get(mfield.type)
				print(f"parse field '{fname}' as '{mfield.type}'")
				if struct:
					try:
						if isinstance(val, models.Model):
							val = struct.serialize_model_object(val, recursive, access)
						elif isinstance(val, BaseManager):
							objects: list['HssiModel'] = val.all()
							val = []
							for obj in objects:
								val.append(struct.serialize_model_object(obj, recursive, access))
						else: val = str(val)
					except Exception as e: print(f"error fetching data for {object}:{fname}, {e}")
				else:
					try: 
						if isinstance(val, models.Model):
							val = val.get_serialized_data(access, recursive)
						elif isinstance(val, BaseManager):
							objects = val.all()
							val = []
							for obj in objects:
								valdat: dict[str: Any] = obj.get_serialized_data(access, recursive)
								for key, dat in list(valdat.items()): 
									if not dat: valdat.pop(key)
								val.append(valdat)

						else: val = str(val)
					except Exception as e: print(f"error fetching data for {object}:{fname}, {e}")
			if val: data[fname] = val

		return data
			
	def serialized(self) -> dict:
		if self.top_field is None:
			warnings.warn(
				f"Serializing model structure {self.type_name} without top_field", 
				UserWarning,
			)
		subfields_prepend = [] if self.top_field is None else [self.top_field.serialized()]
		serialized: dict = {
			"targetModel": self.target_model.__name__,
			"typeName": self.type_name,
			"subfields": [*subfields_prepend, *[
					subfield.serialized()
					for subfield in self.subfields
			]],
		}
		return serialized
	
	def to_json(self) -> str: return json.dumps(self.serialized())

	def __iter__(self):
		yield self.top_field
		yield from self.subfields