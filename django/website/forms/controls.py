from django import forms

from typing import NamedTuple, Type
from ..models import HssiModel

## Utility ---------------------------------------------------------------------

def bool_js_string(value: bool) -> str:
    return "true" if value else "false"

## Combo box -------------------------------------------------------------------

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

    def __init__(self, model: Type[HssiModel], attrs: dict = None):
        super().__init__(attrs)
        self.case_sensitive_filtering = getattr(
            attrs, "case_sensitive_filtering", 
            self.case_sensitive_filtering
        )
        self.multi_select = attrs.get("multi_select", self.multi_select)
        self.filter_on_focus = attrs.get("filter_on_focus", self.filter_on_focus)
        self.dropdown_button = attrs.get("dropdown_button", self.dropdown_button)
        self.dropdown_on_focus = attrs.get("dropdown_on_focus", self.dropdown_on_focus)
        self.dropdown_on_blank = attrs.get("dropdown_on_blank", self.dropdown_on_blank)
        self.model = model

    @classmethod
    def dropdown_selector(
        cls, model: Type[HssiModel], mutli_select = False, attrs: dict = None
    ) -> 'ModelObjectSelector':
        """ creates a dropdown selector for the given model """
        return cls(model, {
            'multi_select': mutli_select,
            'dropdown_button': True,
            'filter_on_focus': False,
            **(attrs or {}),
        })
    
    @classmethod
    def auto_textbox(
        cls, model: Type[HssiModel], mutli_select = False, attrs: dict = None
    ) -> 'ModelObjectSelector':
        """ creates a dropdown selector for the given model"""
        return cls(model, {
            'multi_select': mutli_select,
            'dropdown_on_blank': False,
            'dropdown_on_focus': False,
            **(attrs or {}),
        })

    @classmethod
    def modelbox(
        cls, model: Type[HssiModel], mutli_select = False, attrs: dict = None
    ) -> 'ModelObjectSelector':
        return cls(model, {'multi_select': mutli_select, **(attrs or {}) })

    def get_context(self, name, value, attrs) -> dict:
        context = super().get_context(name, value, attrs)
        context['widget']['choices'] = self.get_choices()
        context['widget']['case_sensitive_filtering'] = bool_js_string(
            self.case_sensitive_filtering
        )
        context['widget']['multi_select'] = bool_js_string(self.multi_select)
        context['widget']['filter_on_focus'] = bool_js_string(self.filter_on_focus)
        context['widget']['dropdown_button'] = bool_js_string(self.dropdown_button)
        context['widget']['dropdown_on_focus'] = bool_js_string(self.dropdown_on_focus)
        context['widget']['dropdown_on_blank'] = bool_js_string(self.dropdown_on_blank)
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