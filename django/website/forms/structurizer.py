"""
This module handles translating the django model structure into serializable
data structures that can be passed to the website frontend modules in
/frontend/forms and be used to generate forms on the clientside that represent
the exposed django model structure
"""

import json

from django.db.models import fields


from typing import Type, TYPE_CHECKING
if TYPE_CHECKING:
    from ..models import HssiModel

class ModelSubfield:
    """
    TODO
    """

    def serialized(self) -> dict:
        # TODO
        return {}
    
    @classmethod
    def create(cls, field: fields.Field) -> 'ModelSubfield':
        # TODO
        pass

class ModelStructure:
    """
    TODO
    """
    
    type_name: str = ""
    top_field: ModelSubfield | None = None
    sub_fields: list[ModelSubfield] = []

    @classmethod
    def create(cls, model: Type[HssiModel]) -> 'ModelStructure':
        """ create a model structure based on the given hssi model class """
        structure = ModelStructure()

        fields = model._meta.get_fields()
        for field in fields:
            # TODO create structure
            print(field.name, type(field))

        return structure
    
    def serialized(self) -> dict:
        serialized: dict = {
            "typeName": self.type_name,
            "topField": self.top_field.serialized() if self.top_field else None,
            "subFields": [],
        }
        serialized
    
    def to_json(self) -> str:
        return json.dumps(self.serialized())
