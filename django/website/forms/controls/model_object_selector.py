import json
from django import forms

from enum import Enum
from typing import NamedTuple, Type

from ...util import RequirementLevel, REQ_LVL_ATTR
from ...models import HssiModel

class ModelObjectChoice(NamedTuple):
	id: str
	name: str
	keywords: list[str]
	tooltip: str

class ModelObjectSelector(forms.TextInput):
	"""
	allows the user to easily select one or multiple of the 
	instances of the model that the modelbox is associated with
	"""
	
	attrs: dict | None
	template_name: str = 'widgets/model_object_selector.html'
	model: Type[HssiModel] | None = None
	filter: dict = {}

	case_sensitive_filtering: bool = False
	multi_select: bool = False
	filter_on_focus: bool = True
	dropdown_button: bool = False
	dropdown_on_focus: bool = True
	dropdown_on_blank: bool = True
	option_tooltips: bool = True
	new_object_field: str | None = None
	requirement_level: RequirementLevel = RequirementLevel.RECOMMENDED

	def __init__(
		self, model: Type[HssiModel], 
		requirement: RequirementLevel = RequirementLevel.RECOMMENDED, 
		attrs: dict = {}
	):
		attrs[REQ_LVL_ATTR] = requirement
		super().__init__(attrs)
		self.case_sensitive_filtering = getattr(
			attrs, "case_sensitive_filtering", 
			self.case_sensitive_filtering
		)
		self.requirement_level = requirement
		self.multi_select = attrs.get("multi_select", self.multi_select)
		self.filter_on_focus = attrs.get("filter_on_focus", self.filter_on_focus)
		self.dropdown_button = attrs.get("dropdown_button", self.dropdown_button)
		self.dropdown_on_focus = attrs.get("dropdown_on_focus", self.dropdown_on_focus)
		self.dropdown_on_blank = attrs.get("dropdown_on_blank", self.dropdown_on_blank)
		self.model = model

	@classmethod
	def dropdown_selector(
		cls, model: Type[HssiModel], mutli_select = False, 
		requirement: RequirementLevel = RequirementLevel.RECOMMENDED, 
		attrs: dict = {}
	) -> 'ModelObjectSelector':
		""" creates a dropdown selector for the given model """
		return cls(model, requirement=requirement, attrs={
			'multi_select': mutli_select,
			'dropdown_button': True,
			'filter_on_focus': False,
			**(attrs or {}),
		})
	
	@classmethod
	def auto_textbox(
		cls, model: Type[HssiModel], mutli_select = False, 
		requirement: RequirementLevel = RequirementLevel.RECOMMENDED, 
		attrs: dict = {}
	) -> 'ModelObjectSelector':
		""" creates a dropdown selector for the given model """
		return cls(model, requirement=requirement, attrs={
			'multi_select': mutli_select,
			'dropdown_on_blank': False,
			'dropdown_on_focus': False,
			**(attrs or {}),
		})

	@classmethod
	def modelbox(
		cls, model: Type[HssiModel], mutli_select = False, 
		requirement: RequirementLevel = RequirementLevel.RECOMMENDED, 
		attrs: dict = {}
	) -> 'ModelObjectSelector':
		return cls(
			model, 
			requirement=requirement, 
			attrs={'multi_select': mutli_select, **(attrs or {}) }
		)

	def get_context(self, name, value, attrs) -> dict:
		attrs[REQ_LVL_ATTR] = self.requirement_level.value
		context = super().get_context(name, value, attrs)

		properties: dict = {
			'requirementLevel': self.requirement_level.value,
			'caseSensitiveFiltering': self.case_sensitive_filtering,
			'multiSelect': self.multi_select,
			'filterOnFocus': self.filter_on_focus,
			'dropdownButton': self.dropdown_button,
			'dropdownOnFocus': self.dropdown_on_focus,
			'dropdownOnBlank': self.dropdown_on_blank,
			'optionTooltips': self.option_tooltips,
			'newObjectField': self.new_object_field,
		}
		context['widget']['properties'] = properties
		context['widget']['properties_json'] = json.dumps(properties)

		choices = self.get_choices()
		context['widget']['choices_json'] = json.dumps([x._asdict() for x in choices])

		return context

	def get_choices(self) -> list[ModelObjectChoice]:
		""" returns a list of all available choices for the model """
		objs = self.model.objects.filter(**self.filter)
		choices = []
		for obj in objs:
			choice = ModelObjectChoice(
				str(obj.id), 
				str(obj),
				obj.get_search_terms(),
				obj.get_tooltip(),
			)
			choices.append(choice)
		
		return choices