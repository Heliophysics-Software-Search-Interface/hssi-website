from ..models import *
from ..util import RequirementLevel
from .names import *


SUBMISSION_FORM_DATA: ModelStructure = ModelStructure.define(
    "SubmissionForm",

    # ----- Sec 1 -----
    # Submitter
    ModelSubfield.define(
        name=FIELD_SUBMITTERNAME, 
        type=TYPE_MODELBOX, 
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
        name=FIELD_PERSISTENTIDENTIFIER,
        type=TYPE_URL,
        requirement=RequirementLevel.RECOMMENDED.value,
        properties={
            PROP_LABEL: "Persistent Identifier",
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
        },
        multi=False,
    ),

    # Authors
    ModelSubfield.define(
        name=FIELD_AUTHORS,
        type=TYPE_MODELBOX,
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
        name=FIELD_SOFTWARENAME,
        type=TYPE_CHAR,
        requirement=RequirementLevel.MANDATORY.value,
        properties={
            PROP_LABEL: "Software Name",
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
        },
        multi=False,
    ),
    # Concise Description
    ModelSubfield.define(
        name="conciseDescription",
        type=TYPE_TEXTAREA,
        requirement=RequirementLevel.OPTIONAL.value,
        properties={
            PROP_LABEL: "Concise Description",
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
        },
        multi=False,
    ),
    # Publisher
    ModelSubfield.define(
        name=FIELD_PUBLISHER,
        type=TYPE_MODELBOX,
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
        name=FIELD_VERSIONNUMBER,
        type=TYPE_MODELBOX,
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
        name=FIELD_PROGRAMMINGLANGUAGE,
        type=TYPE_MODELBOX,
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
        name=FIELD_LICENSE,
        type=TYPE_MODELBOX,
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