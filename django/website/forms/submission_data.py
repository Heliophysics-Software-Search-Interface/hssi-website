from ..models import *
from ..util import RequirementLevel
from .names import *

SUBMISSION_FORM_SUBMITTER: ModelStructure = ModelStructure.define(
	"SubmissionFormSubmitter",
	
	ModelSubfield.define(
		name=FIELD_SUBMITTERNAME, 
		type=TYPE_CHAR,
		requirement=RequirementLevel.MANDATORY.value, 
		properties={
			PROP_LABEL: "Submitter Name",
			PROP_TT_EXPL: TTEXPL_SUBMITTERNAME,
			PROP_TT_BEST: TTBEST_SUBMITTERNAME,
			PROP_WIDGET_PROPS: {
				PROP_TARGET_MODEL: Submitter.__name__
			},
		},
		multi=False,
	),
)

SUBMISSION_FORM_AUTHOR: ModelStructure = ModelStructure.define(
	"SubmissionFormAuthor",
	ModelSubfield.define(
		name=FIELD_AUTHORS,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.MANDATORY.value,
		properties={
			PROP_LABEL: "Authors",
			PROP_TT_EXPL: TTEXPL_AUTHORS,
			PROP_TT_BEST: TTBEST_AUTHORS,
			PROP_WIDGET_PROPS: {
				PROP_TARGET_MODEL: Person.__name__,
			},
		},
		multi=False,
	),
)

SUBMISSION_FORM_VERSION: ModelStructure = ModelStructure.define(
	"SubmissionFormVersion",
	ModelSubfield.define(
		name=FIELD_VERSIONNUMBER,
		type=TYPE_CHAR,
		requirement=RequirementLevel.MANDATORY.value,
		properties={
			PROP_LABEL: "Version Number",
			PROP_TT_EXPL: TTEXPL_VERSIONNUMBER,
			PROP_TT_BEST: TTBEST_VERSIONNUMBER,
			PROP_WIDGET_PROPS: {
				PROP_TARGET_MODEL: SoftwareVersion.__name__,
			},
		},
		multi=False,
	),
)

SUBMISSION_FORM_PUBLICATION: ModelStructure = ModelStructure.define(
	"SubmissionFormPublication",
	ModelSubfield.define(
		name=FIELD_REFERENCEPUBLICATION,
		type=TYPE_URL,
		requirement=RequirementLevel.MANDATORY.value,
		properties={
			PROP_LABEL: "Reference Publication",
			PROP_TT_EXPL: TTEXPL_REFERENCEPUBLICATION,
			PROP_TT_BEST: TTBEST_REFERENCEPUBLICATION,
		},
		multi=False,
	),
)

SUBMISSION_FORM_REL_SOFTWARE: ModelStructure = ModelStructure.define(
	"SubmissionFormRelSoftware",
	ModelSubfield.define(
		name=FIELD_RELATEDSOFTWARE,
		type=TYPE_URL,
		requirement=RequirementLevel.MANDATORY.value,
		properties={
			PROP_LABEL: "Related Software",
		},
		multi=False,
	),
	
)

SUBMISSION_FORM_INSTRUMENT: ModelStructure = ModelStructure.define(
	"SubmissionFormInstrument",
	ModelSubfield.define(
		name=FIELD_RELATEDINSTRUMENTS,
		type=TYPE_CHAR,
		requirement=RequirementLevel.MANDATORY.value,
		properties={
			PROP_LABEL: "Instrument Name",
		},
		multi=False,
	),
)

SUBMISSION_FORM_OBSERVATORY: ModelStructure = ModelStructure.define(
	"SubmissionFormObservatory",
	ModelSubfield.define(
		name=FIELD_RELATEDOBSERVATORIES,
		type=TYPE_CHAR,
		requirement=RequirementLevel.MANDATORY.value,
		properties={
			PROP_LABEL: "Related Observatories",
			PROP_TT_EXPL: TTEXPL_RELATEDOBSERVATORIES,
			PROP_TT_BEST: TTBEST_RELATEDOBSERVATORIES,
		},
		multi=False,
	),
)

SUBMISSION_FORM_DATASET: ModelStructure = ModelStructure.define(
	"SubmissionFormDataset",
	ModelSubfield.define(
		name=FIELD_RELATEDDATASETS,
		type=TYPE_URL,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Related Datasets",
			PROP_TT_EXPL: TTEXPL_RELATEDDATASETS,
			PROP_TT_BEST: TTBEST_RELATEDDATASETS,
		},
		multi=False,
	),
)

SUBMISSION_FORM_LICENSE: ModelStructure = ModelStructure.define(
	"SubmissionFormLicense",
	ModelSubfield.define(
		name=FIELD_LICENSE,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "License",
			PROP_TT_EXPL: TTEXPL_LICENSE,
			PROP_TT_BEST: TTBEST_LICENSE,
			PROP_WIDGET_PROPS: {
				PROP_TARGET_MODEL: License.__name__,
			},
		},
		multi=False,
	),
)

SUBMISSION_FORM_ORGANIZATION: ModelStructure = ModelStructure.define(
	"SubmissionFormOrganization",
	ModelSubfield.define(
		name=FIELD_PUBLISHER,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Organization",
			PROP_WIDGET_PROPS: {
				PROP_TARGET_MODEL: Organization.__name__,
			},
		},
		multi=False,
	),
)

SUBMISSION_FORM_AWARD: ModelStructure = ModelStructure.define(
	"SubmissionFormAward",
	ModelSubfield.define(
		name=FIELD_AWARDTITLE,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Award Title",
			PROP_TT_EXPL: TTEXPL_AWARDTITLE,
			PROP_TT_BEST: TTBEST_AWARDTITLE,
			PROP_WIDGET_PROPS: {
				PROP_TARGET_MODEL: Award.__name__,
			},
		},
		multi=True,
	),
)

SUBMISSION_FORM_FIELDS: ModelStructure = ModelStructure.define(
	"SubmissionForm",

	# ----- Sec 1 -----
	# Submitter
	ModelSubfield.define(
		name=FIELD_SUBMITTERNAME, 
		type=SUBMISSION_FORM_SUBMITTER.type_name, 
		requirement=RequirementLevel.MANDATORY.value, 
		properties={
			PROP_LABEL: "Submitter",
			PROP_TT_EXPL: TTEXPL_SUBMITTERNAME,
			PROP_TT_BEST: TTBEST_SUBMITTERNAME,
			PROP_WIDGET_PROPS: {
				PROP_TARGET_MODEL: Submitter.__name__
			},
		},
		multi=True,
	),

	# PID
	ModelSubfield.define(
		name=FIELD_PERSISTENTIDENTIFIER,
		type=TYPE_URL,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Persistent Identifier",
			PROP_TT_EXPL: TTEXPL_PERSISTENTIDENTIFIER,
			PROP_TT_BEST: TTBEST_PERSISTENTIDENTIFIER,
		},
		multi=False,
	),

	# Code Repo
	ModelSubfield.define(
		name=FIELD_CODEREPOSITORYURL,
		type=TYPE_URL,
		requirement=RequirementLevel.MANDATORY.value,
		properties={
			PROP_LABEL: "Code Repository",
			PROP_TT_EXPL: TTEXPL_CODEREPOSITORYURL,
			PROP_TT_BEST: TTBEST_CODEREPOSITORYURL,
		},
		multi=False,
	),

	# Authors
	ModelSubfield.define(
		name=FIELD_AUTHORS,
		type=SUBMISSION_FORM_AUTHOR.type_name,
		requirement=RequirementLevel.MANDATORY.value,
		properties={
			PROP_LABEL: "Authors",
			PROP_TT_EXPL: TTEXPL_AUTHORS,
			PROP_TT_BEST: TTBEST_AUTHORS,
			PROP_WIDGET_PROPS: {
				PROP_TARGET_MODEL: Person.__name__,
			},
		},
		multi=False,
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
		type=SUBMISSION_FORM_ORGANIZATION.type_name,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Publisher",
			PROP_TT_EXPL: TTEXPL_PUBLISHER,
			PROP_TT_BEST: TTBEST_PUBLISHER,
			PROP_WIDGET_PROPS: {
				PROP_TARGET_MODEL: Organization.__name__,
			},
		},
		multi=False,
	),
	# Version
	ModelSubfield.define(
		name=FIELD_VERSIONNUMBER,
		type=SUBMISSION_FORM_VERSION.type_name,
		requirement=RequirementLevel.MANDATORY.value,
		properties={
			PROP_LABEL: "Version",
			PROP_TT_EXPL: TTEXPL_VERSIONNUMBER,
			PROP_TT_BEST: TTBEST_VERSIONNUMBER,
			PROP_WIDGET_PROPS: {
				PROP_TARGET_MODEL: SoftwareVersion.__name__,
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
				PROP_TARGET_MODEL: ProgrammingLanguage.__name__,
			},
		},
		multi=True,
	),
	# License
	ModelSubfield.define(
		name=FIELD_LICENSE,
		type=SUBMISSION_FORM_LICENSE.type_name,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "License",
			PROP_TT_EXPL: TTEXPL_LICENSE,
			PROP_TT_BEST: TTBEST_LICENSE,
			PROP_WIDGET_PROPS: {
				PROP_TARGET_MODEL: License.__name__,
			},
		},
		multi=False,
	),

	# ----- Sec 2 -----
	# Keywords
	ModelSubfield.define(
		name=FIELD_KEYWORDS,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Keywords",
			PROP_TT_EXPL: TTEXPL_KEYWORDS,
			PROP_TT_BEST: TTBEST_KEYWORDS,
		},
		multi=False,
	),
	# Reference Publication
	ModelSubfield.define(
		name=FIELD_REFERENCEPUBLICATION,
		type=SUBMISSION_FORM_PUBLICATION.type_name,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Reference Publication",
			PROP_TT_EXPL: TTEXPL_REFERENCEPUBLICATION,
			PROP_TT_BEST: TTBEST_REFERENCEPUBLICATION,
		},
		multi=False,
	),
	# Functionality
	ModelSubfield.define(
		name=FIELD_SOFTWAREFUNCTIONALITY,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Software Functionality",
			PROP_TT_EXPL: TTEXPL_SOFTWAREFUNCTIONALITY,
			PROP_TT_BEST: TTBEST_SOFTWAREFUNCTIONALITY,
		},
		multi=True,
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
	# Data Inputs
	ModelSubfield.define(
		name=FIELD_DATAINPUTS,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Data Inputs",
			PROP_TT_EXPL: TTEXPL_DATAINPUTS,
			PROP_TT_BEST: TTBEST_DATAINPUTS,
		},
		multi=True,
	),
	# File Formats
	ModelSubfield.define(
		name=FIELD_SUPPORTEDFILEFORMATS,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Supported File Formats",
			PROP_TT_EXPL: TTEXPL_SUPPORTEDFILEFORMATS,
			PROP_TT_BEST: TTBEST_SUPPORTEDFILEFORMATS,
		},
		multi=True,
	),
	# Development Status
	ModelSubfield.define(
		name=FIELD_DEVELOPMENTSTATUS,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Development Status",
			PROP_TT_EXPL: TTEXPL_DEVELOPMENTSTATUS,
			PROP_TT_BEST: TTBEST_DEVELOPMENTSTATUS,
		},
		multi=False,
	),
	# Operating System
	ModelSubfield.define(
		name=FIELD_OPERATINGSYSTEM,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Operating System",
			PROP_TT_EXPL: TTEXPL_OPERATINGSYSTEM,
			PROP_TT_BEST: TTBEST_OPERATINGSYSTEM,
		},
		multi=True,
	),
	# Related Region
	ModelSubfield.define(
		name=FIELD_RELATEDREGION,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Related Region",
			PROP_TT_EXPL: TTEXPL_RELATEDREGION,
			PROP_TT_BEST: TTBEST_RELATEDREGION,
		},
		multi=True,
	),
	# Funder
	ModelSubfield.define(
		name=FIELD_FUNDER,
		type=SUBMISSION_FORM_ORGANIZATION.type_name,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Funder",
			PROP_TT_EXPL: TTEXPL_FUNDER,
			PROP_TT_BEST: TTBEST_FUNDER,
		},
		multi=False,
	),
	# Awards
	ModelSubfield.define(
		name=FIELD_AWARDTITLE,
		type=SUBMISSION_FORM_AWARD.type_name,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Award Title",
			PROP_TT_EXPL: TTEXPL_AWARDTITLE,
			PROP_TT_BEST: TTBEST_AWARDTITLE,
		},
		multi=True,
	),

	# ----- Sec 3 -----
	# Related Publications
	ModelSubfield.define(
		name=FIELD_RELATEDPUBLICATIONS,
		type=TYPE_MODELBOX,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Related Publications",
			PROP_TT_EXPL: TTEXPL_RELATEDPUBLICATIONS,
			PROP_TT_BEST: TTBEST_RELATEDPUBLICATIONS,
		},
		multi=True,
	),
	# Related Datasets
	ModelSubfield.define(
		name=FIELD_RELATEDDATASETS,
		type=SUBMISSION_FORM_DATASET.type_name,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Related Datasets",
			PROP_TT_EXPL: TTEXPL_RELATEDDATASETS,
			PROP_TT_BEST: TTBEST_RELATEDDATASETS,
		},
		multi=True,
	),
	# Related Software
	ModelSubfield.define(
		name=FIELD_RELATEDSOFTWARE,
		type=SUBMISSION_FORM_REL_SOFTWARE.type_name,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Related Software",
			PROP_TT_EXPL: TTEXPL_RELATEDSOFTWARE,
			PROP_TT_BEST: TTBEST_RELATEDSOFTWARE,
		},
		multi=True,
	),
	# Related Instruments
	ModelSubfield.define(
		name=FIELD_RELATEDINSTRUMENTS,
		type=SUBMISSION_FORM_INSTRUMENT.type_name,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Related Instruments",
			PROP_TT_EXPL: TTEXPL_RELATEDINSTRUMENTS,
			PROP_TT_BEST: TTBEST_RELATEDINSTRUMENTS,
		},
		multi=True,
	),
	# Interoperable Software
	ModelSubfield.define(
		name=FIELD_INTEROPERABLESOFTWARE,
		type=SUBMISSION_FORM_REL_SOFTWARE.type_name,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Interpoerable Software",
			PROP_TT_EXPL: TTEXPL_INTEROPERABLESOFTWARE,
			PROP_TT_BEST: TTBEST_INTEROPERABLESOFTWARE,
		},
		multi=True,
	),
	# Related Observatories
	ModelSubfield.define(
		name=FIELD_RELATEDOBSERVATORIES,
		type=SUBMISSION_FORM_OBSERVATORY.type_name,
		requirement=RequirementLevel.RECOMMENDED.value,
		properties={
			PROP_LABEL: "Related Observatories",
			PROP_TT_EXPL: TTEXPL_RELATEDOBSERVATORIES,
			PROP_TT_BEST: TTBEST_RELATEDOBSERVATORIES,
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
		},
		multi=False,
	),

	# Agreement
	ModelSubfield.define(
		name="agree",
		type=TYPE_CHECKBOX,
		requirement=RequirementLevel.MANDATORY.value,
		properties={
			PROP_LABEL: "Metadata License Agreement",
			PROP_TT_EXPL: "Agree that all metadata you've entered into this form will be freely available for searching and indexing or any other purpose",
		},
		multi=False,
	),
)