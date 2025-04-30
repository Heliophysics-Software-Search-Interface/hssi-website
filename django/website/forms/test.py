from django import forms

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