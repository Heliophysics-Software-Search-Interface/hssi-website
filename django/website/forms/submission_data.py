from ..models import *
from ..util import RequirementLevel
from .names import *

SUBMISSION_FORM_AUTHOR_AFFILIATION: ModelStructure = ModelStructure.define(
	Organization,
	"SubmissionFormAuthorAffiliation",
	ModelSubfield.define(
		name=FIELD_AUTHORAFFILIATION,
		row_name=ROW_ORGANIZATION_NAME,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Organization",
			PROP_WIDGET_PROPS: {
				PROP_TT_EXPL: TTEXPL_AUTHORAFFILIATION,
				PROP_TT_BEST: TTBEST_AUTHORAFFILIATION,
				WPROP_TARGETMODEL: Organization.__name__,
			},
		},
		multi=False,
	),
	ModelSubfield.define(
		name=FIELD_AUTHORAFFILIATIONIDENTIFIER,
		row_name=ROW_ORGANIZATION_IDENTIFIER,
		type=TYPE_ROR,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Affiliation Identifier",
			PROP_TT_EXPL: TTEXPL_AUTHORAFFILIATIONIDENTIFIER,
			PROP_TT_BEST: TTBEST_AUTHORAFFILIATIONIDENTIFIER,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: Organization.__name__,
			},
		},
		multi=False,
	),
)

SUBMISSION_FORM_CONTRIBUTOR_AFFILIATION: ModelStructure = ModelStructure.define(
	Organization,
	"SubmissionFormContributorAffiliation",
	ModelSubfield.define(
		name=FIELD_CONTRIBUTORAFFILIATION,
		row_name=ROW_ORGANIZATION_NAME,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Organization",
			PROP_WIDGET_PROPS: {
				PROP_TT_EXPL: TTEXPL_CONTRIBUTORAFFILIATION,
				PROP_TT_BEST: TTBEST_CONTRIBUTORAFFILIATION,
				WPROP_TARGETMODEL: Organization.__name__,
			},
		},
		multi=False,
	),
	ModelSubfield.define(
		name=FIELD_CONTRIBUTORAFFILIATIONIDENTIFIER,
		row_name=ROW_ORGANIZATION_IDENTIFIER,
		type=TYPE_ROR,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Identifier",
			PROP_TT_EXPL: TTEXPL_CONTRIBUTORAFFILIATIONIDENTIFIER,
			PROP_TT_BEST: TTBEST_CONTRIBUTORAFFILIATIONIDENTIFIER,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: Organization.__name__,
			},
		},
		multi=False,
	),
)

SUBMISSION_FORM_PUBLISHER: ModelStructure = ModelStructure.define(
	Organization,
	"SubmissionFormPublisher",
	ModelSubfield.define(
		name=FIELD_PUBLISHER,
		row_name=ROW_ORGANIZATION_NAME,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Organization",
			PROP_WIDGET_PROPS: {
				PROP_TT_EXPL: TTEXPL_PUBLISHER,
				PROP_TT_BEST: TTBEST_PUBLISHER,
				WPROP_TARGETMODEL: Organization.__name__,
			},
		},
		multi=False,
	),
	ModelSubfield.define(
		name=FIELD_PUBLISHERIDENTIFIER,
		row_name=ROW_ORGANIZATION_IDENTIFIER,
		type=TYPE_ROR,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Publisher Identifier",
			PROP_TT_EXPL: TTEXPL_PUBLISHERIDENTIFIER,
			PROP_TT_BEST: TTBEST_PUBLISHERIDENTIFIER,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: Organization.__name__,
			},
		},
		multi=False,
	),
)

SUBMISSION_FORM_FUNDER: ModelStructure = ModelStructure.define(
	Organization,
	"SubmissionFormFunder",
	ModelSubfield.define(
		name=FIELD_FUNDER,
		row_name=ROW_ORGANIZATION_NAME,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Organization",
			PROP_WIDGET_PROPS: {
				PROP_TT_EXPL: TTEXPL_FUNDER,
				PROP_TT_BEST: TTBEST_FUNDER,
				WPROP_TARGETMODEL: Organization.__name__,
			},
		},
		multi=False,
	),
	ModelSubfield.define(
		name=FIELD_FUNDERIDENTIFIER,
		row_name=ROW_ORGANIZATION_IDENTIFIER,
		type=TYPE_ROR,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Funder Identifier",
			PROP_TT_EXPL: TTEXPL_FUNDERIDENTIFIER,
			PROP_TT_BEST: TTBEST_FUNDERIDENTIFIER,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: Organization.__name__,
			},
		},
		multi=False,
	),
)

SUBMISSION_FORM_SUBMITTER: ModelStructure = ModelStructure.define(
	Submitter,
	"SubmissionFormSubmitter",
	ModelSubfield.define(
		name=FIELD_SUBMITTERNAME, 
		row_name=ROW_PERSON_NAME,
		type=TYPE_CHAR,
		requirement=RequirementLevel.MANDATORY.value, 
		properties={
			PROP_LABEL: "Submitter Name",
			PROP_TT_EXPL: TTEXPL_SUBMITTERNAME,
			PROP_TT_BEST: TTBEST_SUBMITTERNAME,
		},
		multi=False,
	),
	ModelSubfield.define(
		name=FIELD_SUBMITTEREMAIL,
		row_name=ROW_SUBMITTER_EMAIL,
		type=TYPE_EMAIL,
		requirement=RequirementLevel.MANDATORY.value,
		properties={
			PROP_LABEL: "Submitter Email",
			PROP_TT_EXPL: TTEXPL_SUBMITTEREMAIL,
			PROP_TT_BEST: TTBEST_SUBMITTEREMAIL,
		},
		multi=True
	),
)

SUBMISSION_FORM_AUTHOR: ModelStructure = ModelStructure.define(
	Person,
	"SubmissionFormAuthor",
	ModelSubfield.define(
		name=FIELD_AUTHORS,
		row_name=ROW_PERSON_NAME,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.MANDATORY.value, 
		properties={
			PROP_LABEL: "Authors",
			PROP_TT_EXPL: TTEXPL_AUTHORS,
			PROP_TT_BEST: TTBEST_AUTHORS,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: Person.__name__
			},
		},
		multi=False,
	),
	ModelSubfield.define(
		name=FIELD_AUTHORIDENTIFIER,
		row_name=ROW_PERSON_IDENTIFIER,
		type=TYPE_ORCID,
		requirement=RequirementLevel.RECOMMENDED,
		properties={
			PROP_LABEL: "Author Identifier",
			PROP_TT_EXPL: TTEXPL_AUTHORIDENTIFIER,
			PROP_TT_BEST: TTBEST_AUTHORIDENTIFIER,
		},
		multi=False,
	),
	ModelSubfield.define(
		name=FIELD_AUTHORAFFILIATION,
		row_name=ROW_PERSON_AFFILIATION,
		type=SUBMISSION_FORM_AUTHOR_AFFILIATION.type_name,
		requirement=RequirementLevel.RECOMMENDED,
		properties={
			PROP_LABEL: "Affiliation",
			PROP_TT_EXPL: TTEXPL_AUTHORAFFILIATION,
			PROP_TT_BEST: TTBEST_AUTHORAFFILIATION,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: Organization.__name__,
				WPROP_ALLOWNEWENTRIES: True,
			}
		},
		multi=True,
	),
)

SUBMISSION_FORM_CONTRIBUTOR: ModelStructure = ModelStructure.define(
	Person,
	"SubmissionFormContributor",
	ModelSubfield.define(
		name=FIELD_CONTRIBUTOR, 
		row_name=ROW_PERSON_NAME,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.OPTIONAL.value, 
		properties={
			PROP_LABEL: "Contributors",
			PROP_TT_EXPL: TTEXPL_CONTRIBUTOR,
			PROP_TT_BEST: TTBEST_CONTRIBUTOR,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: Person.__name__
			},
		},
		multi=False,
	),
	ModelSubfield.define(
		name=FIELD_CONTRIBUTORIDENTIFIER,
		row_name=ROW_PERSON_IDENTIFIER,
		type=TYPE_ORCID,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Contributor Identifier",
			PROP_TT_EXPL: TTEXPL_CONTRIBUTORIDENTIFIER,
			PROP_TT_BEST: TTBEST_CONTRIBUTORIDENTIFIER,
		},
		multi=False,
	),
	ModelSubfield.define(
		name=FIELD_CONTRIBUTORAFFILIATION,
		row_name=ROW_PERSON_AFFILIATION,
		type=SUBMISSION_FORM_CONTRIBUTOR_AFFILIATION.type_name,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Affiliation",
			PROP_TT_EXPL: TTEXPL_CONTRIBUTORAFFILIATION,
			PROP_TT_BEST: TTBEST_CONTRIBUTORAFFILIATION,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: Organization.__name__,
				WPROP_ALLOWNEWENTRIES: True,
			}
		},
		multi=True,
	),
)

SUBMISSION_FORM_VERSION: ModelStructure = ModelStructure.define(
	SoftwareVersion,
	"SubmissionFormVersion",
	ModelSubfield.define(
		name=FIELD_VERSIONNUMBER,
		row_name=ROW_VERSION_NUMBER,
		type=TYPE_CHAR,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Version Number",
			PROP_TT_EXPL: TTEXPL_VERSIONNUMBER,
			PROP_TT_BEST: TTBEST_VERSIONNUMBER,
			PROP_TOPFIELD: "identifier",
		},
		multi=False,
	),
	ModelSubfield.define(
		name=FIELD_VERSIONDATE,
		row_name=ROW_VERSION_DATE,
		type=TYPE_DATE,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Version Date",
			PROP_TT_EXPL: TTEXPL_VERSIONDATE,
			PROP_TT_BEST: TTBEST_VERSIONDATE,
		},
		multi=False,
	),
	ModelSubfield.define(
		name=FIELD_VERSIONDESCRIPTION,
		row_name=ROW_VERSION_DESCRIPTION,
		type=TYPE_TEXTAREA,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Version Description",
			PROP_TT_EXPL: TTEXPL_VERSIONDESCRIPTION,
			PROP_TT_BEST: TTBEST_VERSIONDESCRIPTION,
		},
		multi=False,
	),
	ModelSubfield.define(
		name=FIELD_VERSIONPID,
		row_name=ROW_VERSION_PID,
		type=TYPE_DATACITEDOI,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Version PID",
			PROP_TT_EXPL: TTEXPL_VERSIONPID,
			PROP_TT_BEST: TTBEST_VERSIONPID,
		},
		multi=False,
	),
)

SUBMISSION_FORM_PUBLICATION: ModelStructure = ModelStructure.define(
	RelatedItem,
	"SubmissionFormPublication",
	ModelSubfield.define(
		name=FIELD_REFERENCEPUBLICATION,
		row_name=ROW_CONTROLLEDLIST_IDENTIFIER,
		type=TYPE_DATACITEDOI,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Reference Publication",
			PROP_TT_EXPL: TTEXPL_REFERENCEPUBLICATION,
			PROP_TT_BEST: TTBEST_REFERENCEPUBLICATION,
			PROP_TOPFIELD: "identifier",
		},
		multi=False,
	),
)

SUBMISSION_FORM_REL_SOFTWARE: ModelStructure = ModelStructure.define(
	RelatedItem,
	"SubmissionFormRelSoftware",
	ModelSubfield.define(
		name=FIELD_RELATEDSOFTWARE,
		row_name=ROW_CONTROLLEDLIST_IDENTIFIER,
		type=TYPE_DATACITEDOI,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Related Software",
			PROP_TOPFIELD: "identifier",
		},
		multi=False,
	),
	
)

SUBMISSION_FORM_INSTRUMENT: ModelStructure = ModelStructure.define(
	InstrumentObservatory,
	"SubmissionFormInstrument",
	ModelSubfield.define(
		name=FIELD_RELATEDINSTRUMENTS,
		row_name=ROW_CONTROLLEDLIST_NAME,
		type=TYPE_CHAR,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Instrument Name",
			PROP_TT_EXPL: TTEXPL_RELATEDINSTRUMENTS,
			PROP_TT_BEST: TTBEST_RELATEDINSTRUMENTS,
		},
		multi=False,
	),
	ModelSubfield.define(
		name=FIELD_RELATEDINSTRUMENTIDENTIFIER,
		row_name=ROW_CONTROLLEDLIST_IDENTIFIER,
		type=TYPE_URL,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Instrument Identifier",
			PROP_TT_EXPL: TTEXPL_RELATEDINSTRUMENTIDENTIFIER,
			PROP_TT_BEST: TTBEST_RELATEDINSTRUMENTIDENTIFIER,
		},
		multi=False,
	),
)

SUBMISSION_FORM_OBSERVATORY: ModelStructure = ModelStructure.define(
	InstrumentObservatory,
	"SubmissionFormObservatory",
	ModelSubfield.define(
		name=FIELD_RELATEDOBSERVATORIES,
		row_name=ROW_CONTROLLEDLIST_NAME,
		type=TYPE_CHAR,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Observatory Name",
			PROP_TT_EXPL: TTEXPL_RELATEDOBSERVATORIES,
			PROP_TT_BEST: TTBEST_RELATEDOBSERVATORIES,
		},
		multi=False,
	),
	ModelSubfield.define(
		name=FIELD_RELATEDINSTRUMENTIDENTIFIER,
		type=TYPE_URL,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Observatory Identifier",
			PROP_TT_EXPL: TTEXPL_RELATEDINSTRUMENTIDENTIFIER,
			PROP_TT_BEST: TTBEST_RELATEDINSTRUMENTIDENTIFIER,
		},
		multi=False,
	),
)

SUBMISSION_FORM_DATASET: ModelStructure = ModelStructure.define(
	RelatedItem,
	"SubmissionFormDataset",
	ModelSubfield.define(
		name=FIELD_RELATEDDATASETS,
		row_name=ROW_CONTROLLEDLIST_IDENTIFIER,
		type=TYPE_DATACITEDOI,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Related Datasets",
			PROP_TT_EXPL: TTEXPL_RELATEDDATASETS,
			PROP_TT_BEST: TTBEST_RELATEDDATASETS,
			PROP_TOPFIELD: "identifier",
			PROP_WIDGET_PROPS: {
				WPROP_ALLOWNEWENTRIES: True,
			}
		},
		multi=False,
	),
)

SUBMISSION_FORM_LICENSE: ModelStructure = ModelStructure.define(
	License,
	"SubmissionFormLicense",
	ModelSubfield.define(
		name=FIELD_LICENSE,
		row_name=ROW_LICENSE_NAME,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "License",
			PROP_TT_EXPL: TTEXPL_LICENSE,
			PROP_TT_BEST: TTBEST_LICENSE,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: License.__name__,
				WPROP_LICENCEMBOX: True,
			},
		},
		multi=False,
	),
	ModelSubfield.define(
		name=FIELD_LICENSEURI,
		row_name=ROW_LICENSE_URL,
		type=TYPE_URL,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "License URI",
			PROP_TT_EXPL: TTEXPL_LICENSEURI,
			PROP_TT_BEST: TTBEST_LICENSEURI,
		},
		multi=False,
	),
)

SUBMISSION_FORM_AWARD: ModelStructure = ModelStructure.define(
	Award,
	"SubmissionFormAward",
	ModelSubfield.define(
		name=FIELD_AWARDTITLE,
		row_name=ROW_AWARD_NAME,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Award Title",
			PROP_TT_EXPL: TTEXPL_AWARDTITLE,
			PROP_TT_BEST: TTBEST_AWARDTITLE,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: Award.__name__,
			},
		},
		multi=True,
	),
	ModelSubfield.define(
		name=FIELD_AWARDNUMBER,
		row_name=ROW_AWARD_IDENTIFIER,
		type=TYPE_CHAR,
		requirement=RequirementLevel.RECOMMENDED,
		properties={
			PROP_LABEL: "Award Number",
			PROP_TT_EXPL: TTEXPL_AWARDNUMBER,
			PROP_TT_BEST: TTBEST_AWARDNUMBER,
		},
		multi=False,
	),
)

## FORM FIELD STRUCTURE DATA ---------------------------------------------------

SUBMISSION_FORM_FIELDS: ModelStructure = ModelStructure.define(
	Software,
	"SubmissionForm",

	# ----- Sec 1 -----
	# Submitter
	ModelSubfield.define(
		name=FIELD_SUBMITTERNAME, 
		row_name=ROW_PERSON_NAME,
		type=SUBMISSION_FORM_SUBMITTER.type_name, 
		requirement=RequirementLevel.MANDATORY.value, 
		properties={
			PROP_LABEL: "Submitter",
			PROP_TT_EXPL: TTEXPL_SUBMITTERNAME,
			PROP_TT_BEST: TTBEST_SUBMITTERNAME,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: Submitter.__name__,
				WPROP_ALLOWNEWENTRIES: True,
			},
		},
		multi=False,
	),
	# PID
	ModelSubfield.define(
		name=FIELD_PERSISTENTIDENTIFIER,
		type=TYPE_AUTOFILLDATACITE,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Persistent Identifier",
			PROP_TT_EXPL: TTEXPL_PERSISTENTIDENTIFIER,
			PROP_TT_BEST: TTBEST_PERSISTENTIDENTIFIER,
			PROP_WIDGET_PROPS: {
				WPROP_RESULTFILTERS: ["software", "concept"]
			}
		},
		multi=False,
	),
	# Code Repo
	ModelSubfield.define(
		name=FIELD_CODEREPOSITORYURL,
		row_name=ROW_SOFTWARE_CODEREPOSITORYURL,
		type=TYPE_AUTOFILLSOMEF,
		requirement=RequirementLevel.MANDATORY.value,
		properties={
			PROP_LABEL: "Code Repository",
			PROP_TT_EXPL: TTEXPL_CODEREPOSITORYURL,
			PROP_TT_BEST: TTBEST_CODEREPOSITORYURL,
		},
		multi=False,
	),
	# Functionality
	ModelSubfield.define(
		name=FIELD_SOFTWAREFUNCTIONALITY,
		row_name=ROW_CONTROLLEDLIST_NAME,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Software Functionality",
			PROP_TT_EXPL: TTEXPL_SOFTWAREFUNCTIONALITY,
			PROP_TT_BEST: TTBEST_SOFTWAREFUNCTIONALITY,
			PROP_WIDGET_PROPS: {
				WPROP_DROPDOWNBUTTON: True,
				WPROP_TARGETMODEL: FunctionCategory.__name__,
			},
		},
		multi=True,
	),
	# Related Region
	ModelSubfield.define(
		name=FIELD_RELATEDREGION,
		row_name=ROW_CONTROLLEDLIST_NAME,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Related Region",
			PROP_TT_EXPL: TTEXPL_RELATEDREGION,
			PROP_TT_BEST: TTBEST_RELATEDREGION,
			PROP_WIDGET_PROPS: {
				WPROP_DROPDOWNBUTTON: True,
				WPROP_TARGETMODEL: Region.__name__,
			},
		},
		multi=True,
	),
	# Authors
	ModelSubfield.define(
		name=FIELD_AUTHORS,
		row_name=ROW_PERSON_NAME,
		type=SUBMISSION_FORM_AUTHOR.type_name,
		requirement=RequirementLevel.MANDATORY.value,
		properties={
			PROP_LABEL: "Authors",
			PROP_TT_EXPL: TTEXPL_AUTHORS,
			PROP_TT_BEST: TTBEST_AUTHORS,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: Person.__name__,
				WPROP_ALLOWNEWENTRIES: True,
			},
		},
		multi=True,
	),	
	# Software Name
	ModelSubfield.define(
		name=FIELD_SOFTWARENAME,
		type=TYPE_CHAR,
		requirement=RequirementLevel.MANDATORY.value,
		properties={
			PROP_LABEL: "Software Name",
			PROP_TT_EXPL: TTEXPL_SOFTWARENAME,
			PROP_TT_BEST: TTBEST_SOFTWARENAME,
		},
		multi=False,
	),
	# Description
	ModelSubfield.define(
		name=FIELD_DESCRIPTION,
		type=TYPE_TEXTAREA,
		requirement=RequirementLevel.MANDATORY.value,
		properties={
			PROP_LABEL: "Description",
			PROP_TT_EXPL: TTEXPL_DESCRIPTION,
			PROP_TT_BEST: TTBEST_DESCRIPTION,
		},
		multi=False,
	),
	# Concise Description
	ModelSubfield.define(
		name=FIELD_CONCISEDESCRIPTION,
		type=TYPE_TEXTAREA,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Concise Description",
			PROP_TT_EXPL: TTEXPL_CONCISEDESCRIPTION,
			PROP_TT_BEST: TTBEST_CONCISEDESCRIPTION,
			PROP_WIDGET_PROPS: {
				WPROP_MAXLENGTH: 200,
			}
		},
		multi=False,
	),
	# Publication Date
	ModelSubfield.define(
		name=FIELD_PUBLICATIONDATE,
		type=TYPE_DATE,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Publication Date",
			PROP_TT_EXPL: TTEXPL_PUBLICATIONDATE,
			PROP_TT_BEST: TTBEST_PUBLICATIONDATE,
		},
		multi=False,
	),
	# Publisher
	ModelSubfield.define(
		name=FIELD_PUBLISHER,
		type=SUBMISSION_FORM_PUBLISHER.type_name,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Publisher",
			PROP_TT_EXPL: TTEXPL_PUBLISHER,
			PROP_TT_BEST: TTBEST_PUBLISHER,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: Organization.__name__,
				WPROP_ALLOWNEWENTRIES: True,
			},
		},
		multi=False,
	),
	# Version
	ModelSubfield.define(
		name=FIELD_VERSIONNUMBER,
		row_name=ROW_SOFTWARE_VERSION,
		type=SUBMISSION_FORM_VERSION.type_name,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Version",
			PROP_TT_EXPL: TTEXPL_VERSIONNUMBER,
			PROP_TT_BEST: TTBEST_VERSIONNUMBER,
			PROP_TOPFIELD: "number",
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: SoftwareVersion.__name__,
				WPROP_ALLOWNEWENTRIES: True,
			},
		},
		multi=False,
	),
	# Programming Language
	ModelSubfield.define(
		name=FIELD_PROGRAMMINGLANGUAGE,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Programming Language",
			PROP_TT_EXPL: TTEXPL_PROGRAMMINGLANGUAGE,
			PROP_TT_BEST: TTBEST_PROGRAMMINGLANGUAGE,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: ProgrammingLanguage.__name__,
				WPROP_DROPDOWNBUTTON: True,
			},
		},
		multi=True,
	),
	# Reference Publication
	ModelSubfield.define(
		name=FIELD_REFERENCEPUBLICATION,
		type=SUBMISSION_FORM_PUBLICATION.type_name,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Reference Publication",
			PROP_TT_EXPL: TTEXPL_REFERENCEPUBLICATION,
			PROP_TT_BEST: TTBEST_REFERENCEPUBLICATION,
			PROP_TOPFIELD: "identifier",
		},
		multi=False,
	),
	# License
	ModelSubfield.define(
		name=FIELD_LICENSE,
		row_name=ROW_LICENSE_NAME,
		type=SUBMISSION_FORM_LICENSE.type_name,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "License",
			PROP_TT_EXPL: TTEXPL_LICENSE,
			PROP_TT_BEST: TTBEST_LICENSE,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: License.__name__,
				WPROP_DROPDOWNBUTTON: True,
				WPROP_ALLOWNEWENTRIES: True,
			},
		},
		multi=False,
	),

	# ----- Sec 2 -----
	# Keywords
	ModelSubfield.define(
		name=FIELD_KEYWORDS,
		row_name=ROW_CONTROLLEDLIST_NAME,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Keywords",
			PROP_TT_EXPL: TTEXPL_KEYWORDS,
			PROP_TT_BEST: TTBEST_KEYWORDS,
			PROP_WIDGET_PROPS: {
				WPROP_DROPDOWNBUTTON: True,
				WPROP_TARGETMODEL: Keyword.__name__,
				WPROP_ALLOWNEWENTRIES: True,
			},
		},
		multi=True,
	),
	# Data Inputs
	ModelSubfield.define(
		name=FIELD_DATASOURCES,
		row_name=ROW_CONTROLLEDLIST_NAME,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Data Sources",
			PROP_TT_EXPL: TTEXPL_DATASOURCES,
			PROP_TT_BEST: TTEXPL_DATASOURCES,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: DataInput.__name__,
				WPROP_DROPDOWNBUTTON: True,
			},
		},
		multi=True,
	),
	# File Formats - input
	ModelSubfield.define(
		name=FIELD_INPUTFORMATS,
		row_name=ROW_CONTROLLEDLIST_NAME,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Input File Formats",
			PROP_TT_EXPL: TTEXPL_INPUTFORMATS,
			PROP_TT_BEST: TTBEST_INPUTFORMATS,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: FileFormat.__name__,
				WPROP_DROPDOWNBUTTON: True,
			},
		},
		multi=True,
	),
	# File Formats - output
	ModelSubfield.define(
		name=FIELD_OUTPUTFORMATS,
		row_name=ROW_CONTROLLEDLIST_NAME,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Output File Formats",
			PROP_TT_EXPL: TTEXPL_OUPUTFORMATS,
			PROP_TT_BEST: TTBEST_OUPUTFORMATS,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: FileFormat.__name__,
				WPROP_DROPDOWNBUTTON: True,
			},
		},
		multi=True,
	),
	# Operating System
	ModelSubfield.define(
		name=FIELD_OPERATINGSYSTEM,
		row_name=ROW_CONTROLLEDLIST_NAME,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Operating System",
			PROP_TT_EXPL: TTEXPL_OPERATINGSYSTEM,
			PROP_TT_BEST: TTBEST_OPERATINGSYSTEM,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: OperatingSystem.__name__,
				WPROP_DROPDOWNBUTTON: True,
			},
		},
		multi=True,
	),
	# CPU Architecture
	ModelSubfield.define(
		name=FIELD_CPUARCHITECTURE,
		row_name=ROW_CONTROLLEDLIST_NAME,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "CPU Architecture",
			PROP_TT_EXPL: TTEXPL_CPUARCHITECTURE,
			PROP_TT_BEST: TTBEST_CPUARCHITECTURE,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: CpuArchitecture.__name__,
				WPROP_DROPDOWNBUTTON: True,
			},
		},
		multi=True,
	),
	# Related Phenomena
	ModelSubfield.define(
		name=FIELD_RELATEDPHENOMENA,
		row_name=ROW_CONTROLLEDLIST_NAME,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Related Phenomena",
			PROP_TT_EXPL: TTEXPL_RELATEDPHENOMENA,
			PROP_TT_BEST: TTBEST_RELATEDPHENOMENA,
			PROP_WIDGET_PROPS:{
				WPROP_DROPDOWNBUTTON: True,
				WPROP_TARGETMODEL: Phenomena.__name__,
				WPROP_ALLOWNEWENTRIES: True,
			}
		},
		multi=True,
	),
	# Development Status
	ModelSubfield.define(
		name=FIELD_DEVELOPMENTSTATUS,
		row_name=ROW_CONTROLLEDLIST_NAME,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Development Status",
			PROP_TT_EXPL: TTEXPL_DEVELOPMENTSTATUS,
			PROP_TT_BEST: TTBEST_DEVELOPMENTSTATUS,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: RepoStatus.__name__,
				WPROP_DROPDOWNBUTTON: True,
			},
		},
		multi=False,
	),
	# Documentation
	ModelSubfield.define(
		name=FIELD_DOCUMENTATION,
		type=TYPE_URL,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Documentation",
			PROP_TT_EXPL: TTEXPL_DOCUMENTATION,
			PROP_TT_BEST: TTBEST_DOCUMENTATION,
		},
		multi=False,
	),
	# Funder
	ModelSubfield.define(
		name=FIELD_FUNDER,
		row_name=ROW_ORGANIZATION_NAME,
		type=SUBMISSION_FORM_FUNDER.type_name,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Funder",
			PROP_TT_EXPL: TTEXPL_FUNDER,
			PROP_TT_BEST: TTBEST_FUNDER,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: Organization.__name__,
				WPROP_ALLOWNEWENTRIES: True,
			},
		},
		multi=True,
	),
	# Awards
	ModelSubfield.define(
		name=FIELD_AWARDTITLE,
		row_name=ROW_SOFTWARE_AWARDTITLE,
		type=SUBMISSION_FORM_AWARD.type_name,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Award Title",
			PROP_TT_EXPL: TTEXPL_AWARDTITLE,
			PROP_TT_BEST: TTBEST_AWARDTITLE,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: Award.__name__,
				WPROP_ALLOWNEWENTRIES: True,
			},
		},
		multi=True,
	),

	# ----- Sec 3 -----
	# Related Publications
	ModelSubfield.define(
		name=FIELD_RELATEDPUBLICATIONS,
		row_name=ROW_CONTROLLEDLIST_NAME,
		type=SUBMISSION_FORM_PUBLICATION.type_name,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Related Publications",
			PROP_TT_EXPL: TTEXPL_RELATEDPUBLICATIONS,
			PROP_TT_BEST: TTBEST_RELATEDPUBLICATIONS,
			PROP_TOPFIELD: "identifier",
			PROP_WIDGET_PROPS: {
				WPROP_RESULTFILTERS: ["notsoftware", "notdataset"],
				WPROP_TARGETMODEL: RelatedItem.__name__,
				WPROP_ALLOWNEWENTRIES: True,
			},
		},
		multi=True,
	),
	# Related Datasets
	ModelSubfield.define(
		name=FIELD_RELATEDDATASETS,
		row_name=ROW_CONTROLLEDLIST_NAME,
		type=SUBMISSION_FORM_DATASET.type_name,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Related Datasets",
			PROP_TT_EXPL: TTEXPL_RELATEDDATASETS,
			PROP_TT_BEST: TTBEST_RELATEDDATASETS,
			PROP_WIDGET_PROPS: {
				WPROP_RESULTFILTERS: ["dataset"],
				WPROP_TARGETMODEL: RelatedItem.__name__,
				WPROP_ALLOWNEWENTRIES: True,
			},
		},
		multi=True,
	),
	# Related Software
	ModelSubfield.define(
		name=FIELD_RELATEDSOFTWARE,
		row_name=ROW_CONTROLLEDLIST_NAME,
		type=SUBMISSION_FORM_REL_SOFTWARE.type_name,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Related Software",
			PROP_TT_EXPL: TTEXPL_RELATEDSOFTWARE,
			PROP_TT_BEST: TTBEST_RELATEDSOFTWARE,
			PROP_WIDGET_PROPS: {
				WPROP_RESULTFILTERS: ["software"],
				WPROP_TARGETMODEL: RelatedItem.__name__,
				WPROP_ALLOWNEWENTRIES: True,
			},
		},
		multi=True,
	),
	# Interoperable Software
	ModelSubfield.define(
		name=FIELD_INTEROPERABLESOFTWARE,
		row_name=ROW_CONTROLLEDLIST_NAME,
		type=SUBMISSION_FORM_REL_SOFTWARE.type_name,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Interoperable Software",
			PROP_TT_EXPL: TTEXPL_INTEROPERABLESOFTWARE,
			PROP_TT_BEST: TTBEST_INTEROPERABLESOFTWARE,
			PROP_WIDGET_PROPS: {
				WPROP_RESULTFILTERS: ["software"],
				WPROP_TARGETMODEL: RelatedItem.__name__,
				WPROP_ALLOWNEWENTRIES: True,
			},
		},
		multi=True,
	),
	# Related Instruments
	ModelSubfield.define(
		name=FIELD_RELATEDINSTRUMENTS,
		row_name=ROW_CONTROLLEDLIST_NAME,
		type=SUBMISSION_FORM_INSTRUMENT.type_name,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Related Instruments",
			PROP_TT_EXPL: TTEXPL_RELATEDINSTRUMENTS,
			PROP_TT_BEST: TTBEST_RELATEDINSTRUMENTS,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: InstrumentObservatory.__name__,
				WPROP_ALLOWNEWENTRIES: True,
			},
		},
		multi=True,
	),
	# Related Observatories
	ModelSubfield.define(
		name=FIELD_RELATEDOBSERVATORIES,
		row_name=ROW_CONTROLLEDLIST_NAME,
		type=SUBMISSION_FORM_OBSERVATORY.type_name,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Related Observatories",
			PROP_TT_EXPL: TTEXPL_RELATEDOBSERVATORIES,
			PROP_TT_BEST: TTBEST_RELATEDOBSERVATORIES,
			PROP_WIDGET_PROPS: {
				WPROP_TARGETMODEL: InstrumentObservatory.__name__,
				WPROP_ALLOWNEWENTRIES: True,
			},
		},
		multi=True,
	),
	# Logo
	ModelSubfield.define(
		name=FIELD_LOGO,
		type=TYPE_URL,
		requirement=RequirementLevel.OPTIONAL.value,
		properties={
			PROP_LABEL: "Logo",
			PROP_TT_EXPL: TTEXPL_LOGO,
			PROP_TT_BEST: TTBEST_LOGO,
			PROP_TOPFIELD: "url",
			PROP_WIDGET_PROPS: {
				WPROP_MAXLENGTH: 2048,
			},
		},
		multi=False,
	),
)

 # Split the subission form into 3 different sections:

[SUBMISSION_FORM_FIELDS_1, SUBMISSION_FORM_FIELDS_2] = SUBMISSION_FORM_FIELDS.split(
	FIELD_KEYWORDS,
	SUBMISSION_FORM_FIELDS.type_name + "_1", 
	SUBMISSION_FORM_FIELDS.type_name + "_2",
)

[SUBMISSION_FORM_FIELDS_2, SUBMISSION_FORM_FIELDS_3] = SUBMISSION_FORM_FIELDS_2.split(
	FIELD_RELATEDPUBLICATIONS,
	SUBMISSION_FORM_FIELDS.type_name + "_2",
	SUBMISSION_FORM_FIELDS.type_name + "_3",
)

register_structure(*[
	SUBMISSION_FORM_AUTHOR_AFFILIATION,
	SUBMISSION_FORM_CONTRIBUTOR_AFFILIATION,
	SUBMISSION_FORM_PUBLISHER,
	SUBMISSION_FORM_FUNDER,
	SUBMISSION_FORM_SUBMITTER,
	SUBMISSION_FORM_AUTHOR,
	SUBMISSION_FORM_CONTRIBUTOR,
	SUBMISSION_FORM_VERSION,
	SUBMISSION_FORM_PUBLICATION,
	SUBMISSION_FORM_REL_SOFTWARE,
	SUBMISSION_FORM_INSTRUMENT,
	SUBMISSION_FORM_OBSERVATORY,
	SUBMISSION_FORM_DATASET,
	SUBMISSION_FORM_LICENSE,
	SUBMISSION_FORM_AWARD,
	SUBMISSION_FORM_FIELDS,
	SUBMISSION_FORM_FIELDS_1,
	SUBMISSION_FORM_FIELDS_2,
	SUBMISSION_FORM_FIELDS_3
])