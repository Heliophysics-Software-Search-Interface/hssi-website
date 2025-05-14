from django import forms
from django.forms.utils import ErrorList

from ..forms import ModelObjectSelector
from ..models import (
    Person, Organization, ProgrammingLanguage, RelatedItem, InstrumentObservatory,
    InstrObsType, Phenomena, DataInput, Functionality
)

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

    field_programming_language = forms.CharField(
        label="Programming Language",
        help_text="The computer programming languages most important for the software.",
    )

    field_publication_date = forms.DateField(
        label="Publication Date", 
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Date of first broadcast/publication."
    )
    
    field_authors = forms.CharField(
        label="Authors", 
        help_text="The author of this content or rating."
    )
    field_publisher = forms.CharField(
        label="Publisher",
        help_text="The publisher (entity) of the creative work.",
    )
    
    field_related_instruments = forms.CharField(
        label="Related Instruments",
        help_text="The instrument the software is designed to support.",
    )
    
    field_related_observatories = forms.CharField(
        label="Related Observatories",
        help_text=(
            "The mission, observatory, and/or group of instruments the software is "
            "designed to support."
        ),
    )

    field_name = forms.CharField(
        label="Software Name",
        help_text="The name of the software",
    )
    
    field_version = forms.CharField(
        label="Software Version",
        help_text="Version of the software instance.",
    )
    
    field_version_date = forms.DateField(
        label="Version Date",
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text="Publication date of the indicated version of the software.",
    )
    
    field_version_description = forms.CharField(
        label="Version Description",
        widget=forms.Textarea,
        help_text=(
            "Description of the change(s) between the last major release and this release. "
            "This description will be shown below the software description on the landing page."
        ),
    )
    
    field_version_pid = forms.URLField(
        label="Version PID",
        help_text=(
            "The globally unique persistent identifier for the specific version of the "
            "software (e.g. the DOI for the version)."
        ),
    )

    field_pid = forms.URLField(
        label="Persistent Identifier",
        help_text=(
            "The globally unique persistent identifier for the software (e.g. the "
            "concept DOI for all versions)."
        ),
    )
    
    field_reference_publication = forms.URLField(
        label="Reference Publication",
        help_text=(
            "The DOI for the publication describing the software, sometimes used as the "
            "preferred citation for the software in addition to the version-specific citation "
            "to the code itself."
        ),
    )
    
    field_description = forms.CharField(
        label="Description",
        widget=forms.Textarea,
        help_text=(
            "A description of the item. The first 150-200 characters will be "
            "used as the preview."
        ),
    )
    
    field_concise_description = forms.CharField(
        label="Concise Description",
        widget=forms.Textarea,
        help_text=(
            "A description of the item limited to 150-200 characters. If the first 150-200 "
            "characters of the description do not provide the desired preview, you may enter "
            "an alternate text here."
        ),
    )

    field_software_functionality = forms.CharField(
        label="Software Functionality",
        help_text="The type of software.",
    )
    
    field_documentation = forms.URLField(
        label="Documentation",
        help_text=(
            "Link to the documentation and installation instructions. If this is the same "
            "as the access URL, then enter that link here."
        ),
    )
    
    field_data_inputs = forms.CharField(
        label="Data Inputs",
        help_text="The data input source the software supports.",
    )
    
    field_file_formats = forms.CharField(
        label="Supported File Formats",
        help_text="The file formats the software supports for data input or output.",
    )
    
    field_related_publications = forms.CharField(
        label="Related Publications",
        help_text=(
            "Publications that describe, cite, or use the software that the software developer"
            " prioritizes but are different from the reference publication."
        ),
    )
    
    field_related_datasets = forms.CharField(
        label="Related Datasets",
        help_text="Datasets the software supports functionality for (e.g. analysis).",
    )

    field_development_status = forms.CharField(
        label="Development Status",
        help_text="The development status of the software.",
    )
    
    field_operating_system = forms.CharField(
        label="Operating System",
        help_text="The operating systems the software supports.",
    )
    
    field_metadata_license = forms.CharField(
        label="Metadata License",
        help_text=(
            "The full name of the license assigned to the metadata (e.g. Creative Commons "
            "Zero v1.0 Universal). Licenses supported by SPDX are preferred. See "
            "https://spdx.org/licenses/ for details."
        ),
    )
    
    field_license = forms.CharField(
        label="License",
        help_text=(
            "The full name of the license assigned to this software (e.g. Apache License "
            "2.0). Lioenses supported by SPDX are preferred. See https://spdx.org/licenses/ "
            "for details. If the software is restricted, please enter 'Restricted' into "
            "this field without the quotes."
        ),
    )
    
    field_related_regions = forms.CharField(
        label="Related Regions",
        help_text="The physical region the software supports science functionality for.",
    )
    
    field_keywords = forms.CharField(
        label="Keywords",
        help_text=(
            "General science keywords relevant for the software (e.g. from the AGU Index List "
            "of the UAT) not supported by other metadata fields."
        ),
    )

    field_related_software = forms.CharField(
        label="Related Software",
        help_text=(
            "Software that performs similar tasks but does not necessarily link together "
            "(which would be considered 'interoperable software'). For example, two software "
            "that model the upper atmosphere of Earth but using different assumptions. "
            "Important software dependencies and software this work was forked from "
            "should also be included here."
        ),
    )
    
    field_intereoperable_software = forms.CharField(
        label="Interoperable Software",
        help_text=""
    )
    
    field_awards = forms.CharField(
        label="Awards",
        help_text="The specific grant or award that funded the work. ",
    )

    field_code_repository = forms.URLField(
        label="Code Repository URL",
        help_text=(
            "Link to the repository where the un-compiled, human readable code and related "
            "code is located (SVN, GitHub, CodePlex, institutional GitLab instance, etc.). "
            "If the software is restricted, put a link to where a potential user could "
            "request access."
        ),
    )
    
    field_logo = forms.URLField(
        label="Logo",
        help_text="A link to the logo for the software.",
    )

    field_related_phenomena = forms.CharField(
        label="Related Phenomena",
        help_text="The phenomena the software supports science functionality for.",
    )

    def __init__(
        self, data=None, files=None, auto_id="id_%s", prefix=None, initial=None,
        error_class=ErrorList, label_suffix=None, empty_permitted=False, field_order=None,
        use_required_attribute=None, renderer=None,
    ): 
        super().__init__(
            data, files, auto_id, prefix, initial, error_class, label_suffix, 
            empty_permitted, field_order, use_required_attribute, renderer
        )

        self.fields['field_programming_language'].widget = (
            ModelObjectSelector.dropdown_selector(
                ProgrammingLanguage, 
                {'multi_select': True}
            )
        )

        self.fields['field_authors'].widget = ModelObjectSelector.auto_textbox(Person)
        self.fields['field_publisher'].widget = ModelObjectSelector.auto_textbox(Organization)

        self.fields['field_related_instruments'].widget = (
            ModelObjectSelector.auto_textbox(InstrumentObservatory)
        )
        self.fields['field_related_instruments'].widget.filter = {
            'type': InstrObsType.INSTRUMENT.value
        }

        self.fields['field_related_observatories'].widget = (
            ModelObjectSelector.auto_textbox(InstrumentObservatory)
        )
        self.fields['field_related_observatories'].widget.filter = {
            'type': InstrObsType.OBSERVATORY.value
        }
