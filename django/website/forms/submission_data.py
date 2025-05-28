from ..models import *
from ..util import RequirementLevel

PROP_LABEL = "label"
PROP_TT_EXPL = "tooltipExplanation"
PROP_TT_BEST = "tooltipBestPractise"

PROP_WIDGET_PROPS = "widgetProperties"
PROP_TARGET_MODEL = "targetModel"
PROP_MODEL_FILTER = "modelFilter"

SUBMISSION_FORM_DATA: ModelStructure = ModelStructure.define(
    "SubmissionForm",

    # ----- Sec 1 -----
    # Submitter
    ModelSubfield.define(
        name="submitter", 
        type="ModelBox", 
        requirement=RequirementLevel.MANDATORY.value, 
        properties={
            PROP_LABEL: "Submitter",
            PROP_WIDGET_PROPS: {
                PROP_TARGET_MODEL: Submitter.__name__
            }
        },
        multi=True,
    ),

    # PID
    ModelSubfield.define(
        name="persistentIdentifier",
        type="UrlWidget",
        requirement=RequirementLevel.RECOMMENDED.value,
        properties={
            PROP_LABEL: "Persistent Identifier",
        },
        multi=False,
    ),

    # Code Repo
    ModelSubfield.define(
        name="codeRepository",
        type="UrlWidget",
        requirement=RequirementLevel.MANDATORY.value,
        properties={
            PROP_LABEL: "Code Repository",
        },
        multi=False,
    ),

    # Authors
    ModelSubfield.define(
        name="authors",
        type="ModelBox",
        requirement=RequirementLevel.MANDATORY.value,
        properties={
            PROP_LABEL: "Authors",
            PROP_WIDGET_PROPS: {
                PROP_TARGET_MODEL: Person.__name__,
            },
        },
        multi=False,
    ),

    # Software Name
    ModelSubfield.define(
        name="softwareName",
        type="CharWidget",
        requirement=RequirementLevel.MANDATORY.value,
        properties={
            PROP_LABEL: "Software Name",
        },
        multi=False,
    ),
    # Description
    ModelSubfield.define(
        name="description",
        type="TextAreaWidget",
        requirement=RequirementLevel.MANDATORY.value,
        properties={
            PROP_LABEL: "Description",
        },
        multi=False,
    ),
    # Concise Description
    ModelSubfield.define(
        name="conciseDescription",
        type="TextAreaWidget",
        requirement=RequirementLevel.OPTIONAL.value,
        properties={
            PROP_LABEL: "Concise Description",
        },
        multi=False,
    ),
    # Publication Date
    ModelSubfield.define(
        name="publicationDate",
        type="DateWidget",
        requirement=RequirementLevel.RECOMMENDED.value,
        properties={
            PROP_LABEL: "Publication Date",
        },
        multi=False,
    ),
    # Publisher
    ModelSubfield.define(
        name="publisher",
        type="ModelBox",
        requirement=RequirementLevel.RECOMMENDED.value,
        properties={
            PROP_LABEL: "Publisher",
            PROP_WIDGET_PROPS: {
                PROP_TARGET_MODEL: Organization.__name__,
            },
        },
        multi=False,
    ),
    # Version
    ModelSubfield.define(
        name="version",
        type="ModelBox",
        requirement=RequirementLevel.MANDATORY.value,
        properties={
            PROP_LABEL: "Version",
            PROP_WIDGET_PROPS: {
                PROP_TARGET_MODEL: SoftwareVersion.__name__,
            },
        },
        multi=False,
    ),
    # Programming Language
    ModelSubfield.define(
        name="programmingLanguage",
        type="ModelBox",
        requirement=RequirementLevel.RECOMMENDED.value,
        properties={
            PROP_LABEL: "Programming Language",
            PROP_WIDGET_PROPS: {
                PROP_TARGET_MODEL: ProgrammingLanguage.__name__,
            },
        },
        multi=True,
    ),
    # License
    ModelSubfield.define(
        name="license",
        type="ModelBox",
        requirement=RequirementLevel.RECOMMENDED.value,
        properties={
            PROP_LABEL: "License",
            PROP_WIDGET_PROPS: {
                PROP_TARGET_MODEL: License.__name__,
            },
        },
        multi=False,
    ),

    # ----- Sec 2 -----
    # Keywords
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),
    ## Reference Publication
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),
    ## Functionality
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),
    ## Documentation
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),
    ## Data Inputs
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),
    ## File Formats
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),
    ## Development Status
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),
    ## Operating System
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),
    ## Related Region
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),
    ## Funder
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),
    ## Awards
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),

    ## ----- Sec 3 -----
    ## Related Publications
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),
    ## Related Datasets
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),
    ## Related Software
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),
    ## Related Instruments
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),
    ## Interoperable Software
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),
    ## Related Observatories
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),
    ## Logo
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),

    ## Agreement
    #ModelSubfield.define(
    #    name="",
    #    type="",
    #    requirement=RequirementLevel.RECOMMENDED.value,
    #    properties={
    #        PROP_LABEL: "",
    #    },
    #    multi=False,
    #),
)