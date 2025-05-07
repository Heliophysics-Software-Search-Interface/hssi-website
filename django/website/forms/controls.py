from django import forms

from typing import NamedTuple, Type
from ..models import HssiModel

## Combo box -------------------------------------------------------------------

class ModelObjectChoice(NamedTuple):
    id: str
    name: str
    keywords: list[str]

class ModelObjectSelector(forms.TextInput):
    """
    allows the user to easily select one or multiple of the 
    instances of the model that the combobox is associated with
    """
    attrs: dict | None
    template_name: str = 'widgets/model_object_selector.html'
    model: Type[HssiModel] | None = None
    case_sensitive_filtering: bool = False
    filter: dict = {}

    def __init__(self, model: Type[HssiModel], attrs: dict = None):
        super().__init__(attrs)
        self.model = model

    def get_context(self, name, value, attrs) -> dict:
        context = super().get_context(name, value, attrs)
        context['widget']['choices'] = self.get_choices()
        context['widget']['case_sensitive'] = self.case_sensitive_filtering
        return context

    def get_choices(self) -> list[ModelObjectChoice]:
        """ returns a list of all available choices for the model """
        objs = self.model.objects.filter(**self.filter)
        choices = []
        for obj in objs:
            choice = ModelObjectChoice(
                str(obj.id), 
                str(obj),
                obj.get_search_terms()
            )
            choices.append(choice)
        
        return choices