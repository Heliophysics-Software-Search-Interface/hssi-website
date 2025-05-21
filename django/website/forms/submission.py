from django import forms
from django.forms.utils import ErrorList

from ..forms import ModelObjectSelector, RequirementLevel, REQ_LVL_ATTR
from ..models import (
    Person, Organization, ProgrammingLanguage, RelatedItem, InstrumentObservatory,
    InstrObsType, Phenomena, DataInput, Functionality, RepoStatus, License,
    OperatingSystem, RelatedItemType, Award, Region, FileFormat
)

class SubmissionForm(forms.Form):
    
    field_code_repository = forms.URLField(
        label="Code Repository URL",
        widget=forms.URLInput(attrs={REQ_LVL_ATTR: RequirementLevel.MANDATORY}),
    )

    field_name = forms.CharField(
        label="Software Name",
        widget=forms.TextInput(attrs={REQ_LVL_ATTR: RequirementLevel.MANDATORY}),
    )

    field_programming_language = forms.CharField(label="Programming Language")

    field_publication_date = forms.DateField(
        label="Publication Date", 
        widget=forms.DateInput(
            attrs={'type': 'date', REQ_LVL_ATTR: RequirementLevel.RECOMMENDED},
        ),
    )

    field_authors = forms.CharField(label="Authors")

    field_publisher = forms.CharField(label="Publisher")

    field_funder = forms.CharField(label="Funder")

    field_development_status = forms.CharField(label="Development Status")

    field_license = forms.CharField(label="License")

    field_operating_system = forms.CharField(label="Operating System")

    field_pid = forms.URLField(
        label="Persistent Identifier",
        widget=forms.URLInput(attrs={REQ_LVL_ATTR: RequirementLevel.RECOMMENDED}),
    )

    field_documentation = forms.URLField(
        label="Documentation",
        widget=forms.URLInput(attrs={REQ_LVL_ATTR: RequirementLevel.RECOMMENDED}),
    )

    field_description = forms.CharField(
        label="Description",
        widget=forms.Textarea(attrs={REQ_LVL_ATTR: RequirementLevel.MANDATORY}),
    )

    field_concise_description = forms.CharField(
        label="Concise Description",
        max_length=200,
        widget=forms.Textarea(attrs={
            'maxlength': 200, 'rows': 3, 
            REQ_LVL_ATTR: RequirementLevel.OPTIONAL,
        }),
    )

    field_related_instruments = forms.CharField(label="Related Instruments")

    field_related_observatories = forms.CharField(label="Related Observatories")

    field_version = forms.CharField(
        label="Version Number",
        widget=forms.TextInput(attrs={REQ_LVL_ATTR: RequirementLevel.RECOMMENDED}),
    )

    field_version_date = forms.DateField(
        label="Version Date",
        widget=forms.DateInput(attrs={'type': 'date', REQ_LVL_ATTR: RequirementLevel.RECOMMENDED}),
    )

    field_version_description = forms.CharField(
        label="Version Description",
        widget=forms.Textarea(attrs={REQ_LVL_ATTR: RequirementLevel.RECOMMENDED}),
    )

    field_version_pid = forms.URLField(
        label="Version PID",
        widget=forms.URLInput(attrs={REQ_LVL_ATTR: RequirementLevel.RECOMMENDED}),
    )

    field_reference_publication = forms.URLField(
        label="Reference Publication",
        widget=forms.URLInput(attrs={REQ_LVL_ATTR: RequirementLevel.MANDATORY}),
    )
    
    field_related_publications = forms.CharField(label="Related Publications")

    field_awards = forms.CharField(label="Awards")

    field_logo = forms.URLField(
        label="Logo",
        widget=forms.URLInput(attrs={REQ_LVL_ATTR: RequirementLevel.OPTIONAL}),
    )
    
    field_software_functionality = forms.CharField(label="Software Functionality")

    field_data_inputs = forms.CharField(label="Data Inputs")
    
    field_related_datasets = forms.CharField(label="Related Datasets")

    field_related_software = forms.CharField(label="Related Software")

    field_intereoperable_software = forms.CharField(label="Interoperable Software")

    field_keywords = forms.CharField(label="Keywords")

    field_related_regions = forms.CharField(label="Related Regions")

    field_file_formats = forms.CharField(label="Supported File Formats")

    field_related_phenomena = forms.CharField(label="Related Phenomena")

    ## Not needed - instead there should be a checkbox to allow users to consent 
    ## to always the same license for the metadata
    # field_metadata_license = forms.CharField(label="Metadata License")
    field_consent = forms.BooleanField(
        label="Consent to Share Metadata",
        widget=forms.CheckboxInput(attrs={REQ_LVL_ATTR: RequirementLevel.MANDATORY}),
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
            ModelObjectSelector.dropdown_selector(ProgrammingLanguage, True)
        )

        self.fields['field_authors'].widget = ModelObjectSelector.auto_textbox(Person, True)
        self.fields['field_publisher'].widget = ModelObjectSelector.auto_textbox(Organization, True)

        self.fields['field_development_status'].widget = (
            ModelObjectSelector.dropdown_selector(RepoStatus)
        )

        self.fields['field_license'].widget = (
            ModelObjectSelector.modelbox(License)
        )

        self.fields['field_operating_system'].widget = (
            ModelObjectSelector.dropdown_selector(OperatingSystem, True)
        )

        self.fields['field_related_instruments'].widget = (
            ModelObjectSelector.auto_textbox(InstrumentObservatory, True)
        )
        self.fields['field_related_instruments'].widget.filter = {
            'type': InstrObsType.INSTRUMENT.value
        }

        self.fields['field_related_observatories'].widget = (
            ModelObjectSelector.auto_textbox(InstrumentObservatory, True)
        )
        self.fields['field_related_observatories'].widget.filter = {
            'type': InstrObsType.OBSERVATORY.value
        }

        self.fields['field_related_publications'].widget = (
            ModelObjectSelector.auto_textbox(RelatedItem, True)
        )
        self.fields['field_related_publications'].widget.filter = {
            'type': RelatedItemType.PUBLICATION.value
        }

        self.fields['field_awards'].widget = (
            ModelObjectSelector.auto_textbox(Award, True)
        )
        
        self.fields['field_software_functionality'].widget = (
            ModelObjectSelector.modelbox(Functionality, True)
        )

        self.fields['field_data_inputs'].widget = (
            ModelObjectSelector.modelbox(DataInput, True)
        )

        self.fields['field_related_datasets'].widget = (
            ModelObjectSelector.auto_textbox(RelatedItem, True)
        )
        self.fields['field_related_datasets'].widget.filter = {
            'type': RelatedItemType.DATASET.value
        }

        self.fields['field_related_software'].widget = (
            ModelObjectSelector.auto_textbox(RelatedItem, True)
        )
        self.fields['field_related_software'].widget.filter = {
            'type': RelatedItemType.SOFTWARE.value
        }

        self.fields['field_intereoperable_software'].widget = (
            ModelObjectSelector.auto_textbox(RelatedItem, True)
        )
        self.fields['field_intereoperable_software'].widget.filter = {
            'type': RelatedItemType.SOFTWARE.value
        }

        self.fields['field_keywords'].widget = (
            ModelObjectSelector.auto_textbox(Phenomena, True)
        )

        self.fields['field_related_regions'].widget = (
            ModelObjectSelector.auto_textbox(Region, True)
        )

        self.fields['field_file_formats'].widget = (
            ModelObjectSelector.auto_textbox(FileFormat, True)
        )

        self.fields['field_related_phenomena'].widget = (
            ModelObjectSelector.auto_textbox(Phenomena, True)
        )

        self.set_tooltips()

    def set_tooltips(self):
        self.fields['field_code_repository'].tt_explanation = "Link to the repository where the un-compiled, human readable code and related code is located (SVN, GitHub, CodePlex, institutional GitLab instance, etc.). If the software is restricted, put a link to where a potential user could request access."
        self.fields['field_code_repository'].tt_best_practice = "Navigate to the root page of your repository, copy the entire link, and paste it into this field."

        self.fields['field_programming_language'].tt_explanation = "The computer programming languages most important for the software."
        self.fields['field_programming_language'].tt_best_practice = "Select the most important languages of the software (e.g. Python, Fortran, C), then enter any other needed details, e.g. the flavor of Fortran. This is not meant to be an exhaustive list."
        
        self.fields['field_publication_date'].tt_explanation = "Date of first broadcast/publication."
        self.fields['field_publication_date'].tt_best_practice = "Used for the initial version of the software. The publication date should be in ISO 8601 format, basically the year, month, and day of the month separated by dashes: YYYY-MM-DD."
        
        self.fields['field_authors'].tt_explanation = "The author of this software."
        self.fields['field_authors'].tt_best_practice = "Minimum should be Last name, first initial. Multiple authors should be included in separate author fields or separated by semicolons (e.g. Smith, J; Ferrari, A.M.)."
        
        self.fields['field_publisher'].tt_explanation = "The publisher (entity) of the creative work."
        self.fields['field_publisher'].tt_best_practice = "For software where a DOI has been obtained through Zenodo, such as through the GitHub-Zenodo workflow, Zenodo is the correct entry. If no DOI has been obtained, indicate the code repository here, such as GitHub or GitLab."
        
        self.fields['field_funder'].tt_explanation = "A person or organization that supports (sponsors) something through some kind of financial contribution."
        self.fields['field_funder'].tt_best_practice = "The name of the organization that provided the funding, e.g. NASA or The Sloan Foundation."
        
        self.fields['field_related_instruments'].tt_explanation = "The instrument the software is designed to support."
        self.fields['field_related_instruments'].tt_best_practice = "Begin typing the item's name in the box. Instruments listed in the IVOA will appear in a dropdown list, please choose the correct one. If your instrument is not listed, please type in the full name."
        
        self.fields['field_related_observatories'].tt_explanation = "The mission, observatory, and/or group of instruments the software is designed to support."
        self.fields['field_related_observatories'].tt_best_practice = "Begin typing the item's name in the box. Missions and Observatories listed in the IVOA will appear in a dropdown list, please choose the correct one. If your mission or observatory is not listed, please type in the full name."
        
        self.fields['field_name'].tt_explanation = "The name of the software."
        self.fields['field_name'].tt_best_practice = "The name of the software package as listed on the code repository."
        
        self.fields['field_version'].tt_explanation = "Version of the software instance."
        self.fields['field_version'].tt_best_practice = "The version number of the software is often an alphanumeric value, which should be easily accessible on the code repository page, e.g. v1.0.0"
        
        self.fields['field_version_date'].tt_explanation = "Publication date of the indicated version of the software."
        self.fields['field_version_date'].tt_best_practice = "The version publication date should be in ISO 8601 format, basically the year, month, and day of the month separated by dashes: YYYY-MM-DD."
        
        self.fields['field_version_description'].tt_explanation = "Description of the change(s) between the last major release and this release. This description will be shown below the software description on the landing page."
        self.fields['field_version_description'].tt_best_practice = "The version description should be a brief summary of the major changes in the new version, such as deprecated and new functionalities, new features, resolved bugs, and so on."
        
        self.fields['field_version_pid'].tt_explanation = "The globally unique persistent identifier for the specific version of the software (e.g. the DOI for the version)."
        self.fields['field_version_pid'].tt_best_practice = "If the software version already has a DOI, please enter the full DOI here, e.g. https://doi.org/10.5281/zenodo.13287868. Entering the DOI also enables us to automatically populate metadata in our system from that DOI. "
        
        self.fields['field_pid'].tt_explanation = "The globally unique persistent identifier for the software (e.g. the concept DOI for all versions)."
        self.fields['field_pid'].tt_best_practice = "If the software already has a DOI, please enter the full DOI here, e.g. https://doi.org/10.5281/zenodo.13287868. Entering the DOI also enables us to automatically populate metadata in our system from that DOI. "
        
        self.fields['field_reference_publication'].tt_explanation = "The DOI for the publication describing the software, sometimes used as the preferred citation for the software in addition to the version-specific citation to the code itself."
        self.fields['field_reference_publication'].tt_best_practice = "Please enter the DOI for the publication describing the software here, such as the DOI for a JOSS paper. "
        
        self.fields['field_description'].tt_explanation = "A description of the item. The first 150-200 characters will be used as the preview."
        self.fields['field_description'].tt_best_practice = "The description of the software should be sufficiently detailed to provide the potential user with the information to determine if the software is useful to their work. The description should include what the software does, why to use this software, any assumptions the software makes, and similar information. The description should ideally be written with proper capitalization, grammar, and punctuation."
        
        self.fields['field_concise_description'].tt_explanation = "A description of the item limited to 150-200 characters. If the first 150-200 characters of the description do not provide the desired preview, you may enter an alternate text here."
        self.fields['field_concise_description'].tt_best_practice = "The text here should be short and provide a concise preview of the longer description."
        
        self.fields['field_software_functionality'].tt_explanation = "The type of software."
        self.fields['field_software_functionality'].tt_best_practice = "Select all types of software functionalities that apply to the software."
        
        self.fields['field_documentation'].tt_explanation = "Link to the documentation and installation instructions. If this is the same as the access URL, then enter that link here."
        self.fields['field_documentation'].tt_best_practice = "Documentation link, including the installation instructions. Should be entered as a complete URL. "
        
        self.fields['field_data_inputs'].tt_explanation = "The data input source the software supports."
        self.fields['field_data_inputs'].tt_best_practice = "Please select all the data input sources the software supports from the list. If a data input source your software supports is not listed, please select 'Other'. If the data input source is observatory specific, please select 'observatory-specific' and make sure to indicate the name of the observatory, mission, or group of instruments in the Related Observatory field."
        
        self.fields['field_file_formats'].tt_explanation = "The file formats the software supports for data input or output."
        self.fields['field_file_formats'].tt_best_practice = "Please select all the file formats that your software supports for either input files or files the software generates. Only file formats supported by the software should be indicated."
        
        self.fields['field_related_publications'].tt_explanation = "Publications that describe, cite, or use the software that the software developer prioritizes but are different from the reference publication."
        self.fields['field_related_publications'].tt_best_practice = "Please enter the DOIs for all publications the software is cited in separated by semicolons(;). If the DOI is not available for a given publication, please enter the citation for the dataset in APA format including a permanent link to the resource, e.g. Shaifullah, G., Tiburzi, C., & Zucca, P. (2020) CMEchaser, Detecting Line-of-Sight Occultations Due to Coronal Mass Ejections Solar Physics, 295(10), 136. https://arxiv.org/abs/2008.12153. "
        
        self.fields['field_related_datasets'].tt_explanation = "Datasets the software supports functionality for (e.g. analysis)."
        self.fields['field_related_datasets'].tt_best_practice = "At minimum, the DOI included here should be the publication that described the dataset. If the DOI is not available for a given dataset, please enter the citation for the dataset in APA format, e.g. Fuselier et al. (2022). MMS 4 Hot Plasma Composition Analyzer (HPCA) Ions, Level 2 (L2), Burst Mode, 0.625 s Data [Data set]. NASA Space Physics Data Facility. https://hpde.io/NASA/NumericalData/MMS/4/HotPlasmaCompositionAnalyzer/Burst/Level2/Ion/PT0.625S.html. "
        
        self.fields['field_development_status'].tt_explanation = "The development status of the software."
        self.fields['field_development_status'].tt_best_practice = "Please select the development status of the code repository from the list below. See repostatus.org for a description of the terms."
        
        self.fields['field_operating_system'].tt_explanation = "The operating systems the software supports."
        self.fields['field_operating_system'].tt_best_practice = "Please select all the operating systems the software can successfully be installed on."
        
        self.fields['field_license'].tt_explanation = "The full name of the license assigned to this software (e.g. Apache License 2.0). Licenses supported by SPDX are preferred. See https://spdx.org/licenses/ for details. If the software is restricted, please enter 'Restricted' into this field without the quotes."
        self.fields['field_license'].tt_best_practice = "Choose from a list of license that you want attributed to your work (e.g. Apache License 2.0) using proper grammer and punctuation. If you select 'Other', please enter the complete title of the license and include version information if applicable. If the license if listed on https://spdx.org/licenses/, please make sure to copy the entire license title."
        
        self.fields['field_related_regions'].tt_explanation = "The physical region the software supports science functionality for."
        self.fields['field_related_regions'].tt_best_practice = "Please select all physical regions the software's functionality is commonly used or intended for."
        
        self.fields['field_keywords'].tt_explanation = "General science keywords relevant for the software (e.g. from the AGU Index List of the UAT) not supported by other metadata fields."
        self.fields['field_keywords'].tt_best_practice = "Begin typing the keyword in the box. Keywords listed in the UAT and AGU Index lists will appear in a dropdown list, please choose the correct one(s). If your keyword is not listed, please type it in."
        
        self.fields['field_related_software'].tt_explanation = "Software that performs similar tasks but does not necessarily link together (which would be considered 'interoperable software'). For example, two software that model the upper atmosphere of Earth but using different assumptions. Important software dependencies and software this work was forked from should also be included here."
        self.fields['field_related_software'].tt_best_practice = "Ideally, the DOI for the software code should be entered here. Otherwise, the link to the code repository can be entered here instead, e.g., https://github.com/sunpy/sunpy. If there is no public code repository, please enter a link where potential users can find more information about the software, such as the link to the related HSSI page. Publication DOIs describing the indicated software should not be listed here, but rather in the relatedPublications field."
        
        self.fields['field_intereoperable_software'].tt_explanation = "Software that interoperates with this software."
        self.fields['field_intereoperable_software'].tt_best_practice = "Ideally, the DOI for the software code should be entered here. Otherwise, the link to the code repository can be entered here instead, e.g., https://github.com/sunpy/sunpy. If there is no public code repository, please enter a link where potential users can find more information about the software, such as the link to the related HSSI page. Publication DOIs describing the indicated software should not be listed here, but rather in the relatedPublications field."
        
        self.fields['field_awards'].tt_explanation = "The specific grant or award that funded the work."
        self.fields['field_awards'].tt_best_practice = "Please copy the full title of the award here."
        
        self.fields['field_logo'].tt_explanation = "A link to the logo for the software."
        self.fields['field_logo'].tt_best_practice = "The logo for the software should be stored online in a permanent place and made publicly accessible."
        
        self.fields['field_related_phenomena'].tt_explanation = "The phenomena the software supports science functionality for."
        self.fields['field_related_phenomena'].tt_best_practice = "Please select phenomena terms from a supported controlled vocabulary."

        self.fields['field_consent'].tt_explanation = "Without consent, we cannot accept the submission."
        self.fields['field_consent'].tt_best_bractise =  "Consent to metadata filled out in this form to be indexed and searchable."
