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

from typing import Type, TYPE_CHECKING
if TYPE_CHECKING:
    from .roots import HssiModel

class ModelSubfield:
    """
    TODO
    """

    name: str = ""
    type: str = ""
    requirement: RequirementLevel = RequirementLevel.OPTIONAL
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
            'requirement': self.requirement.value,
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
                case widgets.TextInput(): subfield.type = "CharWidget"
                case widgets.Textarea(): subfield.type = "TextAreaWidget"
                case widgets.URLInput(): subfield.type = "UrlWidget"
                case widgets.DateInput(): subfield.type = "DateWidget"
                case widgets.CheckboxInput(): subfield.type = "CheckboxWidget"
        
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
        structure.subfields = model.get_subfields()

        return structure
    
    def serialized(self) -> dict:
        serialized: dict = {
            "typeName": self.type_name,
            "topField": self.top_field.serialized() if self.top_field else None,
            "subFields": [
                subfield.serialized()
                for subfield in self.subfields
            ],
        }
        return serialized
    
    def to_json(self) -> str:
        return json.dumps(self.serialized())
