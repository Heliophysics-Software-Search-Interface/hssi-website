"""
This module handles translating the django model structure into serializable
data structures that can be passed to the website frontend modules in
/frontend/forms and be used to generate forms on the clientside that represent
the exposed django model structure
"""

import json

from django.db import models
from django.db.models.fields import related
from django.forms import widgets

from ..util import RequirementLevel, REQ_LVL_ATTR

from enum import StrEnum
from typing import Type, TYPE_CHECKING
if TYPE_CHECKING:
    from .roots import HssiModel

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

        subfield = ModelSubfield()
        subfield.name = field.name

        if isinstance(field, related.RelatedField):
            subfield.multi = True
            subfield.type = field.related_model.__name__

        else:
            # TODO this form field stuff doesn't really do what I want
            widget: widgets.Widget = field.formfield().widget
            subfield.requirement = RequirementLevel(
                widget.attrs.get(REQ_LVL_ATTR, RequirementLevel.OPTIONAL.value)
            )
            subfield.properties = widget.attrs.copy()
            match widget:
                case widgets.TextInput(): subfield.type = WidgetPrimitiveName.char.value
                case widgets.NumberInput(): subfield.type = WidgetPrimitiveName.number.value
                case widgets.Textarea(): subfield.type = WidgetPrimitiveName.textArea.value
                case widgets.URLInput(): subfield.type = WidgetPrimitiveName.url.value
                case widgets.EmailInput(): subfield.type = WidgetPrimitiveName.email.value
                case widgets.DateInput(): subfield.type = WidgetPrimitiveName.date.value
                case widgets.CheckboxInput(): subfield.type = WidgetPrimitiveName.checkbox.value
        
        return subfield

class ModelStructure:
    """
    TODO
    """
    
    type_name: str = ""
    top_field: ModelSubfield | None = None
    subfields: list[ModelSubfield] = []

    @classmethod
    def create(cls, model: Type['HssiModel']) -> 'ModelStructure':
        """ create a model structure based on the given hssi model class """

        structure = ModelStructure()
        structure.type_name = model.__name__
        structure.top_field = ModelSubfield.create(model.get_top_field())
        structure.subfields = [
            ModelSubfield.create(subfield)
            for subfield in model.get_subfields()
        ] 

        return structure
    
    def serialized(self) -> dict:
        subfields_prepend = [] if self.top_field is None else [self.top_field.serialized()]
        serialized: dict = {
            "typeName": self.type_name,
            "subfields": [subfields_prepend, *[
                    subfield.serialized()
                    for subfield in self.subfields
            ]],
        }
        return serialized
    
    def to_json(self) -> str:
        return json.dumps(self.serialized())
