import uuid

from django import forms
from django.db import models

from typing import NamedTuple

## Combo box -------------------------------------------------------------------

class ComboBoxChoice(NamedTuple):
    id: str
    name: str
    keywords: list[str]

class ComboBox(forms.TextInput):
    """
    allows the user to easily select one or multiple of the 
    instances of the model that the combobox is associated with
    """
    attrs: dict | None
    template_name: str = 'controls/combo_box.html'
    choices: list[ComboBoxChoice] = []

    def __init__(self, choices: list[ComboBoxChoice] = [], attrs: dict = None):
        super().__init__(attrs)
        self.choices = choices

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['choices'] = self.choices
        return context