from django import forms
from django.forms.utils import ErrorList

from ..forms import ComboBoxChoice, ComboBox
from ..models import Person

class TestForm(forms.Form):
    
    boolean_field = forms.BooleanField(label="BooleanField", required=False)
    choice_field = forms.ChoiceField(
        label="ChoiceField",
        choices=[('', '---'), ('a', 'Option A'), ('b', 'Option B')]
    )
    multiple_choice_field = forms.MultipleChoiceField(
        label="MultipleChoiceField",
        choices=[('x', 'Choice X'), ('y', 'Choice Y')],
        widget=forms.CheckboxSelectMultiple
    )
    
    char_field = forms.CharField(label="CharField")
    integer_field = forms.IntegerField(label="IntegerField")
    email_field = forms.EmailField(label="EmailField")
    textarea_field = forms.CharField(
        label="TextArea",
        widget=forms.Textarea
    )
    
    date_field = forms.DateField(label="DateField", widget=forms.DateInput(attrs={'type': 'date'}))
    time_field = forms.TimeField(label="TimeField", widget=forms.TimeInput(attrs={'type': 'time'}))
    datetime_field = forms.DateTimeField(
        label="DateTimeField", widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )

    choice_field2 = forms.ChoiceField(
        label="ChoiceField2",
        choices=[('', '---'), ('a', 'Option A'), ('b', 'Option B')]
    )

    combo_box = forms.CharField(label="ComboBox")

    def __init__(
        self, 
        data=None,
        files=None,
        auto_id="id_%s",
        prefix=None,
        initial=None,
        error_class=ErrorList,
        label_suffix=None,
        empty_permitted=False,
        field_order=None,
        use_required_attribute=None,
        renderer=None,
    ):

        super().__init__(
            data, 
            files, 
            auto_id,
            prefix,
            initial, 
            error_class, 
            label_suffix, 
            empty_permitted, 
            field_order, 
            use_required_attribute, 
            renderer
        )

        self.fields['combo_box'].widget = ComboBox(   
            [
                ComboBoxChoice(
                    str(person.id), 
                    str(person), 
                    [person.firstName, person.lastName]
                )
                for person in Person.objects.all()
            ]
        )