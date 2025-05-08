from django import forms
from django.forms.utils import ErrorList

from ..forms import ModelObjectSelector
from ..models import Person, Organization

class TestForm(forms.Form):
    
#    boolean_field = forms.BooleanField(label="BooleanField", required=False)

#    multiple_choice_field = forms.MultipleChoiceField(
#        label="MultipleChoiceField",
#        choices=[('x', 'Choice X'), ('y', 'Choice Y')],
#        widget=forms.CheckboxSelectMultiple
#    )
#    
#    char_field = forms.CharField(label="CharField")
#    integer_field = forms.IntegerField(label="IntegerField")
#    email_field = forms.EmailField(label="EmailField")
#    textarea_field = forms.CharField(
#        label="TextArea",
#        widget=forms.Textarea
#    )
#    
#    time_field = forms.TimeField(label="TimeField", widget=forms.TimeInput(attrs={'type': 'time'}))
#    datetime_field = forms.DateTimeField(
#        label="DateTimeField", widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
#    )
#
#    choice_field2 = forms.ChoiceField(
#        label="ChoiceField2",
#        choices=[('', '---'), ('a', 'Option A'), ('b', 'Option B')]
#    )

    field_programming_language = forms.ChoiceField(
        label="Programming Language",
        choices=[
            ('', '---'), 
            ('a', 'C'), 
            ('b', 'C++'),
            ('c', 'C#'),
            ('d', 'Python'),
            ('e', 'Fortran'),
            ('f', 'Julia'),
            ('g', 'Java'),
            ('h', 'JavaScript'),
            ('i', 'MATLAB'),
            ('j', 'SQL'),
            ('k', 'IDL'),
            ('l', 'Other'),
        ]
    )
    field_pub_date = forms.DateField(label="Publication Date", widget=forms.DateInput(attrs={'type': 'date'}))
    field_authors = forms.CharField(label="Authors")
    field_publisher = forms.CharField(label="Publisher")
    field_related_instruments = forms.CharField(label="Related Instruments")
    field_related_observatories = forms.CharField(label="Related Observatories")

    field_name = forms.CharField(label = "Software Name")
    field_version = forms.CharField(label = "Software Version")
    field_version_date = forms.DateField(label = "Version Date", widget=forms.DateInput(attrs={'type': 'date'}))
    field_version_description = forms.CharField(label="Version Description", widget=forms.Textarea)
    field_version_pid = forms.URLField(label = "Version PID")

    field_pid = forms.URLField(label = "Persistent Identifier")
    field_ref_pub = forms.URLField(label = "Reference Publication")
    field_description = forms.CharField(label = "Description", widget=forms.Textarea)
    field_description_concise = forms.CharField(label = "Concise Description", widget=forms.Textarea)

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

        self.fields['field_authors'].widget = ModelObjectSelector(
            Person, {
                'dropdown_on_blank': False,
            }
        )

        self.fields['field_publisher'].widget = ModelObjectSelector(
            Organization, {
                'dropdown_on_blank': False,
            }
        )