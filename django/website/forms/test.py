from django import forms

class TestForm(forms.Form):
    test_input = forms.CharField(label="Test Input")
    test_select = forms.ChoiceField(
        choices=[('a', 'Option A'), ('b', 'Option B')],
        label="Test Select"
    )