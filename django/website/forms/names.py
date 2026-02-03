from ..models import *

PROP_LABEL = "label"
PROP_TT_EXPL = "tooltipExplanation"
PROP_TT_BEST = "tooltipBestPractise"
PROP_WIDGET_PROPS = "widgetProperties"
PROP_TOPFIELD = "topField"

WPROP_MAXLENGTH = "maxLength"
WPROP_TARGETMODEL = "targetModel"
WPROP_MODELFILTER = "modelFilter"
WPROP_DROPDOWNBUTTON = "dropdownButton"
WPROP_ALLOWNEWENTRIES = "allowNewEntries"
WPROP_RESULTFILTERS = "resultFilters"
WPROP_LICENCEMBOX = "licenseModelbox"

TYPE_CHAR = "CharWidget"
TYPE_TEXTAREA = "TextAreaWidget"
TYPE_URL = "UrlWidget"
TYPE_DATE = "DateWidget"
TYPE_EMAIL = "EmailWidget"
TYPE_CHECKBOX = "CheckboxWidget"
TYPE_AUTOFILLSOMEF = "AutofillSomefWidget"
TYPE_AUTOFILLDATACITE = "AutofillDataciteWidget"
TYPE_ROR = "RorWidget"
TYPE_ORCID = "OrcidWidget"
TYPE_DATACITEDOI = "DataciteDoiWidget"
TYPE_MODELBOX = "ModelBox"

FIELD_PERSISTENTIDENTIFIER = "persistentIdentifier"
FIELD_PROGRAMMINGLANGUAGE = "programmingLanguage"
FIELD_PUBLICATIONDATE = "publicationDate"
FIELD_AUTHORS = "authors"
FIELD_AUTHORIDENTIFIER = "authorIdentifier"
FIELD_AUTHORAFFILIATION = "authorAffiliation"
FIELD_AUTHORAFFILIATIONIDENTIFIER = "authorAffiliationIdentifier"
FIELD_CONTRIBUTOR = "contributor"
FIELD_CONTRIBUTORIDENTIFIER = "contributorIdentifier"
FIELD_CONTRIBUTORAFFILIATION = "contributorAffiliation"
FIELD_CONTRIBUTORAFFILIATIONIDENTIFIER = "contributorAffiliationIdentifier"
FIELD_PUBLISHER = "publisher"
FIELD_PUBLISHERIDENTIFIER = "publisherIdentifier"
FIELD_RELATEDINSTRUMENTS = "relatedInstruments"
FIELD_RELATEDINSTRUMENTIDENTIFIER = "relatedInstrumentIdentifier"
FIELD_RELATEDOBSERVATORIES = "relatedObservatories"
FIELD_SOFTWARENAME = "softwareName"
FIELD_VERSIONNUMBER = "versionNumber"
FIELD_VERSIONDATE = "versionDate"
FIELD_VERSIONDESCRIPTION = "versionDescription"
FIELD_VERSIONPID = "versionPID"
FIELD_REFERENCEPUBLICATION = "referencePublication"
FIELD_DESCRIPTION = "description"
FIELD_CONCISEDESCRIPTION = "conciseDescription"
FIELD_SOFTWAREFUNCTIONALITY = "softwareFunctionality"
FIELD_DOCUMENTATION = "documentation"
FIELD_DATASOURCES = "dataSources"
FIELD_INPUTFORMATS = "inputFormats"
FIELD_OUTPUTFORMATS = "outputFormats"
FIELD_RELATEDPUBLICATIONS = "relatedPublications"
FIELD_RELATEDDATASETS = "relatedDatasets"
FIELD_RELATEDDATASETNAME = "relatedDatasetName"
FIELD_DEVELOPMENTSTATUS = "developmentStatus"
FIELD_OPERATINGSYSTEM = "operatingSystem"
FIELD_CPUARCHITECTURE = "cpuArchitecture"
FIELD_METADATALICENSE = "metadataLicense"
FIELD_METADATALICENSEURI = "metadatalicenseURI"
FIELD_METADATALICENSEIDENTIFIER = "metadatalicenseIdentifier"
FIELD_METADATALICENSEIDENTIFIERSCHEME = "metadatalicenseIdentifierScheme"
FIELD_METADATASCHEMEURI = "metadataschemeURI"
FIELD_LICENSE = "license"
FIELD_LICENSEURI = "licenseURI"
FIELD_LICENSEFILEURL = "licenseFileURL"
FIELD_LICENSEIDENTIFIER = "licenseIdentifier"
FIELD_LICENSEIDENTIFIERSCHEME = "licenseIdentifierScheme"
FIELD_SCHEMEURI = "schemeURI"
FIELD_RELATEDREGION = "relatedRegion"
FIELD_KEYWORDS = "keywords"
FIELD_RELATEDSOFTWARE = "relatedSoftware"
FIELD_INTEROPERABLESOFTWARE = "interoperableSoftware"
FIELD_FUNDER = "funder"
FIELD_FUNDERIDENTIFIER = "funderIdentifier"
FIELD_AWARDTITLE = "awardTitle"
FIELD_AWARDNUMBER = "awardNumber"
FIELD_CODEREPOSITORYURL = "codeRepositoryURL"
FIELD_LOGO = "logo"
FIELD_RELATEDPHENOMENA = "relatedPhenomena"
FIELD_SUBMITTERNAME = "submitterName"
FIELD_SUBMITTEREMAIL = "submitterEmail"
FIELD_CURATORNAME = "curatorName"
FIELD_CURATOREMAIL = "curatorEmail"

ROW_PERSON_NAME = "fullName"
ROW_PERSON_IDENTIFIER = "identifier"
ROW_PERSON_AFFILIATION = "affiliation"
ROW_SUBMITTER_EMAIL = "email"
ROW_ORGANIZATION_NAME = "name"
ROW_ORGANIZATION_IDENTIFIER = "identifier"
ROW_VERSION_NUMBER = "number"
ROW_VERSION_DATE = "release_date"
ROW_VERSION_DESCRIPTION = "description"
ROW_VERSION_PID = "version_pid"
ROW_LICENSE_NAME = "name"
ROW_LICENSE_URL = "url"
ROW_CONTROLLEDLIST_NAME = "name"
ROW_CONTROLLEDLIST_IDENTIFIER = "identifier"
ROW_CONTROLLEDLIST_DEFINITION = "definition"
ROW_AWARD_NAME = "name"
ROW_AWARD_IDENTIFIER = "identifier"
ROW_RELATEDITEM_TYPE = "type"
ROW_SOFTWARE_VERSION = "version"
ROW_SOFTWARE_CODEREPOSITORYURL = "codeRepositoryUrl"
ROW_SOFTWARE_AWARDTITLE = "award"

TTEXPL_PROGRAMMINGLANGUAGE = "The computer programming languages most important for the software."
TTEXPL_PUBLICATIONDATE = "Date of first broadcast/publication. "
TTEXPL_AUTHORS = "The author of this software."
TTEXPL_AUTHORAFFILIATION = "The affiliation of the author, such as an institution or other entity."
TTEXPL_AUTHORAFFILIATIONIDENTIFIER = "The identifier of the affiliation entity, such as the ROR, if one exists."
TTEXPL_AUTHORIDENTIFIER = "The identifier of the author, such as the ORCiD."
TTEXPL_CONTRIBUTOR = "A contributor to this software."
TTEXPL_CONTRIBUTORAFFILIATION = "The affiliation of the contributor, such as an institution or other entity."
TTEXPL_CONTRIBUTORAFFILIATIONIDENTIFIER = "The identifier of the affiliation entity, such as the ROR, if one exists."
TTEXPL_CONTRIBUTORIDENTIFIER = "The identifier of the contributor, such as the ORCiD."
TTEXPL_PUBLISHER = "The publisher (entity) of the creative work."
TTEXPL_PUBLISHERIDENTIFIER = "The identifier of the publisher, such as the ROR. Note that Zenodo does not have an ROR, so the URL should be included instead."
TTEXPL_RELATEDINSTRUMENTS = "The instrument the software is designed to support."
TTEXPL_RELATEDINSTRUMENTIDENTIFIER = "The globally unique persisent identifier associated with the instrument, such as a DOI."
TTEXPL_RELATEDOBSERVATORIES = "The mission, observatory, and/or group of instruments the software is designed to support."
TTEXPL_SOFTWARENAME = "The name of the software"
TTEXPL_VERSIONNUMBER = "Version of the software instance."
TTEXPL_VERSIONDATE = "Publication date of the indicated version of the software."
TTEXPL_VERSIONDESCRIPTION = "Description of the change(s) between the last major release and this release. This description will be shown below the software description on the landing page."
TTEXPL_VERSIONPID = "The globally unique persistent identifier for the specific version of the software (e.g. the DOI for the version)."
TTEXPL_PERSISTENTIDENTIFIER = "The globally unique persistent identifier for the software (e.g. the concept DOI for all versions)."
TTEXPL_REFERENCEPUBLICATION = "The DOI for the publication describing the software, sometimes used as the preferred citation for the software in addition to the version-specific citation to the code itself."
TTEXPL_DESCRIPTION = "A description of the item. The first 150-200 characters will be used as the preview."
TTEXPL_CONCISEDESCRIPTION = "A description of the item limited to 150-200 characters. If the first 150-200 characters of the description do not provide the desired preview, you may enter an alternate text here."
TTEXPL_SOFTWAREFUNCTIONALITY = "The type of software."
TTEXPL_DOCUMENTATION = "Link to the documentation and installation instructions. If this is the same as the access URL, then enter that link here."
TTEXPL_DATASOURCES = "The data input source the software supports."
TTEXPL_INPUTFORMATS = "The file formats the software supports for data input."
TTEXPL_OUPUTFORMATS = "The file formats the software supports for data output."
TTEXPL_RELATEDPUBLICATIONS = "Publications that describe, cite, or use the software that the software developer prioritizes but are different from the reference publication."
TTEXPL_RELATEDDATASETS = "Datasets the software supports functionality for (e.g. analysis)."
TTEXPL_RELATEDDATASETNAME = "Name of the related dataset."
TTEXPL_DEVELOPMENTSTATUS = "The development status of the software."
TTEXPL_OPERATINGSYSTEM = "The operating systems the software supports."
TTEXPL_CPUARCHITECTURE = "The CPU architecture the software requires."
TTEXPL_METADATALICENSE = "The full name of the license assigned to the metadata (e.g. Creative Commons Zero v1.0 Universal). Licenses supported by SPDX are preferred. See https://spdx.org/licenses/ for details."
TTEXPL_METADATALICENSEURI = "The URI of the license (e.g. https://spdx.org/licenses/CC0-1.0.html)"
TTEXPL_METADATALICENSEIDENTIFIER = "A short, standardized version of the license name (e.g. CC0-1.0)."
TTEXPL_METADATALICENSEIDENTIFIERSCHEME = "The name of the scheme (e.g. SPDX)."
TTEXPL_METADATASCHEMEURI = "The URI of the rightsIdentifierScheme (e.g. https://spdx.org/licenses/)."
TTEXPL_LICENSE = "The full name of the license assigned to this software (e.g. Apache License 2.0). Lioenses supported by SPDX are preferred. See https://spdx.org/licenses/ for details. If the software is restricted, please enter 'Restricted' into this field without the quotes."
TTEXPL_LICENSEURI = "The URI of the license (e.g. https://spdx.org/licenses/Apache-2.0.html)"
TTEXPL_LICENSEFILEURL = "The URL of the license file on the code repository."
TTEXPL_LICENSEIDENTIFIER = "A short, standardized version of the license name (e.g. Apache-2.0)."
TTEXPL_LICENSEIDENTIFIERSCHEME = "The name of the scheme (e.g. SPDX)."
TTEXPL_SCHEMEURI = "The URI of the rightsIdentifierScheme (e.g. https://spdx.org/licenses/)."
TTEXPL_RELATEDREGION = "The physical region the software supports science functionality for."
TTEXPL_KEYWORDS = "General science keywords relevant for the software (e.g. from the AGU Index List of the UAT) not supported by other metadata fields."
TTEXPL_RELATEDSOFTWARE = "Software that performs similar tasks but does not necessarily link together (which would be considered 'interoperable software'). For example, two software that model the upper atmosphere of Earth but using different assumptions. Important software dependencies and software this work was forked from should also be included here."
TTEXPL_INTEROPERABLESOFTWARE = "Other important software packages this software has demonstrated interoperability with. Can run package in the same environment as the others w/o errors."
TTEXPL_FUNDER = "A person or organization that supports (sponsors) something through some kind of financial contribution."
TTEXPL_FUNDERIDENTIFIER = "The ROR for the funder. (See ror.org to search for this information.)"
TTEXPL_AWARDTITLE = "The title of the specific grant or award that funded the work. "
TTEXPL_AWARDNUMBER = "The award number or other identifier associated with the award."
TTEXPL_CODEREPOSITORYURL = "Link to the repository where the un-compiled, human readable code and related code is located (SVN, GitHub, CodePlex, institutional GitLab instance, etc.). If the software is restricted, put a link to where a potential user could request access."
TTEXPL_LOGO = "A link to the logo for the software."
TTEXPL_RELATEDPHENOMENA = "The phenomena the software supports science functionality for."
TTEXPL_SUBMITTERNAME = "The name of the person who submitted the metadata."
TTEXPL_SUBMITTEREMAIL = "The work email address of the metadata record submitter."
TTEXPL_CURATORNAME = "The name of the person(s) who reviewed the metadata."
TTEXPL_CURATOREMAIL = "The work email address of the person who reviewed the metadata."

TTBEST_PROGRAMMINGLANGUAGE = "Select the most important languages of the software (e.g. Python, Fortran, C). This is not meant to be an exhaustive list."
TTBEST_PUBLICATIONDATE = "Used for the initial version of the software."
TTBEST_AUTHORS = "Multiple authors should be included in separate author fields."
TTBEST_AUTHORAFFILIATION = "Please enter the complete name of the affiliated entity without using acronyms (e.g. Center for Astrophysics Harvard & Smithsonian). If you have more than one affiliation, please enter them separately."
TTBEST_AUTHORAFFILIATIONIDENTIFIER = "Please enter the complete identifier for each affiliation separately if one exists, e.g. https://ror.org/03c3r2d17. "
TTBEST_AUTHORIDENTIFIER = "Please enter the complete identifier, e.g. https://orcid.org/0000-0003-0875-2023."
TTBEST_CONTRIBUTOR = "Multiple contributors should be included in separate contributor fields"
TTBEST_CONTRIBUTORAFFILIATION = "Please enter the complete name of the affiliated entity without using acronyms (e.g. Center for Astrophysics Harvard & Smithsonian). If you have more than one affiliation, please enter them separately."
TTBEST_CONTRIBUTORAFFILIATIONIDENTIFIER = "Please enter the complete identifier for each affiliation separately if one exists, e.g. https://ror.org/03c3r2d17. "
TTBEST_CONTRIBUTORIDENTIFIER = "Please enter the complete identifier, e.g. https://orcid.org/0000-0003-0875-2023."

TTBEST_PUBLISHER = "For software where a DOI has been obtained through Zenodo, such as through the GitHub-Zenodo workflow, Zenodo is the correct entry. If no DOI has been obtained, indicate the repository host, such as GitHub or GitLab."
TTBEST_PUBLISHERIDENTIFIER = "Please enter the complete identifier, e.g. https://ror.org/03c3r2d17 when the publisher has a ROR or the URL (e.g. https://zenodo.org) otherwise."
TTBEST_RELATEDINSTRUMENTS = "Begin typing the item's name in the box. Instruments listed in the IVOA will appear in a dropdown list, please choose the correct one. If your instrument is not listed, please type in the full name."
TTBEST_RELATEDINSTRUMENTIDENTIFIER = "If the instrument has a DOI, please enter the full DOI here, e.g. https://doi.org/10.5281/zenodo.13287868. Entering the DOI enables us to improve the linking of your software to the referenced instrument."
TTBEST_RELATEDOBSERVATORIES = "Begin typing the item's name in the box. Missions and Observatories listed in the IVOA will appear in a dropdown list, please choose the correct one. If your mission or observatory is not listed, please type in the full name."
TTBEST_SOFTWARENAME = "The name of the software package as listed on the code repository."
TTBEST_VERSIONNUMBER = "The version number of the software is often an alphanumeric value, which should be easily accessible on the code repository page, e.g. v1.0.0."
TTBEST_VERSIONDATE = "Version date should represent the date that the specified version was released."
TTBEST_VERSIONDESCRIPTION = "The version description should be a brief summary of the major changes in the new version, such as deprecated and new functionalities, new features, resolved bugs, and so on."
TTBEST_VERSIONPID = "If the software version already has a DOI, please enter the full DOI here, e.g. https://doi.org/10.5281/zenodo.13287868. Entering the DOI also enables us to automatically populate metadata in our system from that DOI. "
TTBEST_PERSISTENTIDENTIFIER = "If the software already has a concept DOI, please enter the full DOI here, e.g. https://doi.org/10.5281/zenodo.13287868. Entering the concept DOI also enables us to automatically populate metadata in our system from that DOI."
TTBEST_REFERENCEPUBLICATION = "Please enter the DOI for the publication describing the software here, such as the DOI for a JOSS paper. "
TTBEST_DESCRIPTION = "The description of the software should be sufficiently detailed to provide the potential user with the information to determine if the software is useful to their work. The description should include what the software does, why to use this software, any assumptions the software makes, and similar information. The description should ideally be written with proper capitalization, grammar, and punctuation."
TTBEST_CONCISEDESCRIPTION = "The text here should be short and provide a concise preview of the longer description."
TTBEST_SOFTWAREFUNCTIONALITY = "Select all software functionalities that apply. Be as exhaustive as possible—these selections determine which filters and search results your software appears in."
TTBEST_DOCUMENTATION = "Documentation link, including the installation instructions. Should be entered as a complete URL. "
TTBEST_DATASOURCES = "Please select all the data input sources the software supports from the list. If a data input source your software supports is not listed, please select 'Other'. If the data input source is observatory specific, please select 'observatory-specific' and make sure to indicate the name of the observatory, mission, or group of instruments in the Related Observatory field."
TTBEST_INPUTFORMATS = "Please select all the file formats that your software supports for input files. Only file formats supported by the software should be indicated."
TTBEST_OUPUTFORMATS = "Please select all the file formats that your software supports for files the software generates. Only file formats supported by the software should be indicated."
TTBEST_RELATEDPUBLICATIONS = "Please enter the DOIs for all publications the software is cited in separate fields. If the DOI is not available for a given publication, please enter the citation for the dataset in APA format including a permanent link to the resource, e.g. Shaifullah, G., Tiburzi, C., & Zucca, P. (2020) CMEchaser, Detecting Line-of-Sight Occultations Due to Coronal Mass Ejections Solar Physics, 295(10), 136. https://arxiv.org/abs/2008.12153. "
TTBEST_RELATEDDATASETS = "At minimum, the DOI included here should be the publication that described the dataset. If the DOI is not available for a given dataset, please enter the citation for the dataset in APA format, e.g. Fuselier et al. (2022). MMS 4 Hot Plasma Composition Analyzer (HPCA) Ions, Level 2 (L2), Burst Mode, 0.625 s Data [Data set]. NASA Space Physics Data Facility. https://spase-metadata.org/NASA/NumericalData/MMS/4/HotPlasmaCompositionAnalyzer/Burst/Level2/Ion/PT0.625S.html. "
TTBEST_RELATEDDATASETNAME = "Include the mission or observatory name, the instrument name, the data processing level, and any other characteristics that are needed to distinguish the dataset from other datasets produced by the same mission/observatory and instrument. If the dataset is not based on data from a mission or observatory, include descriptive terms such as processing methods or time cadence. The name should be unique to the dataset."
TTBEST_DEVELOPMENTSTATUS = "Please select the development status of the code repository from the list below. See repostatus.org for a description of the terms."
TTBEST_OPERATINGSYSTEM = "Please select all the operating systems the software can successfully be installed on."
TTBEST_CPUARCHITECTURE = "Please select all the CPU architectures the software can successfully be installed and executed on."
TTBEST_METADATALICENSE = "Will always be 'Creative Commons Zero v1.0 Universal' for HSSI metadata."
TTBEST_METADATALICENSEURI = "This field will be automatically populated for CC0."
TTBEST_METADATALICENSEIDENTIFIER = "This field will be automatically populated for CC0."
TTBEST_METADATALICENSEIDENTIFIERSCHEME = "This field will be automatically populated for CC0."
TTBEST_METADATASCHEMEURI = "This field will be automatically populated for CC0."
TTBEST_LICENSE = "Choose from a list of license that you want attributed to your work (e.g. Apache License 2.0) using proper grammer and punctuation. If the license if listed on https://spdx.org/licenses/, please make sure to copy the entire license title."
TTBEST_LICENSEURI = "If you chose a license from the list above or another license included in the SPDX listing, this field will be automatically populated. Otherwise, please enter the URI for the license, e.g. https://spdx.org/licenses/Apache-2.0.html."
TTBEST_LICENSEFILEURL = "If the license file on your code repository has been modified from the original, please copy the link to that file here, e.g. https://github.com/sunpy/sunpy/blob/main/LICENSE.rst."
TTBEST_LICENSEIDENTIFIER = "If you chose a license from the list above or another license included in the SPDX listing, this field will be automatically populated. Otherwise, please enter the identifier for the license, e.g. Apache-2.0."
TTBEST_LICENSEIDENTIFIERSCHEME = "If you chose a license from the list above or another license included in the SPDX listing, this field will be automatically populated. Otherwise, please enter the identifier for the license, e.g. SPDX."
TTBEST_SCHEMEURI = "If you chose a license from the list above or another license included in the SPDX listing, this field will be automatically populated. Otherwise, please enter the identifier for the license, e.g. https://spdx.org/licenses/."
TTBEST_RELATEDREGION = "Please select all physical regions the software's functionality is commonly used or intended for."
TTBEST_KEYWORDS = "Begin typing the keyword in the box. Keywords listed in the UAT and AGU Index lists will appear in a dropdown list, please choose the correct one(s). If your keyword is not listed, please type it in."
TTBEST_RELATEDSOFTWARE = "Ideally, the DOI for the software code should be entered here. Otherwise, the link to the code repository can be entered here instead, e.g., https://github.com/sunpy/sunpy. If there is no public code repository, please enter a link where potential users can find more information about the software, such as the link to the related HSSI item. Publication DOIs describing the indicated software should not be listed here, but rather in the relatedPublications field."
TTBEST_INTEROPERABLESOFTWARE = "Ideally, the DOI for the software code should be entered here. Otherwise, the link to the code repository can be entered here instead, e.g., https://github.com/sunpy/sunpy. If there is no public code repository, please enter a link where potential users can find more information about the software, such as the link to the related HSSI page. Publication DOIs describing the indicated software should not be listed here, but rather in the relatedPublications field."
TTBEST_FUNDER = "The name of the organization that provided the funding, e.g. NASA or The Sloan Foundation."
TTBEST_FUNDERIDENTIFIER = "If the entity that provided funding for this software has an identifier, please copy the full identifier here, e.g. https://ror.org/027ka1x80."
TTBEST_AWARDTITLE = "Please copy the full title of the award here."
TTBEST_AWARDNUMBER = "Please copy the identifier associated with the award here, e.g. NNG19PQ28C. This is used by funding agencies and organizations to track the impact of their funding."
TTBEST_CODEREPOSITORYURL = "Navigate to the root page of your repository, copy the entire link, and paste it into this field."
TTBEST_LOGO = "The logo for the software should be stored online in a permanent place and made publicly accessible."
TTBEST_RELATEDPHENOMENA = "Please select phenomena terms from a supported controlled vocabulary."
TTBEST_SUBMITTERNAME = "Given name, initials, and last/surname (e.g. Jack L. Doe)."
TTBEST_SUBMITTEREMAIL = "Please ensure that a complete email address is given."
TTBEST_CURATORNAME = "Last/surname, given name and initials (e.g. Doe, Jack L.)."
TTBEST_CURATOREMAIL = "Please ensure that a complete email address is given."

# TODO give a proper solution for mapping field names to database rows on frontend
MODEL_FIELD_MAP = {
	FIELD_PERSISTENTIDENTIFIER: "persistentIdentifier",
	FIELD_PROGRAMMINGLANGUAGE: "programmingLanguage",
	FIELD_PUBLICATIONDATE: "publicationDate",
	FIELD_AUTHORS: "authors",
	FIELD_AUTHORIDENTIFIER: "identifier",
	FIELD_AUTHORAFFILIATION: "affiliation",
	FIELD_AUTHORAFFILIATIONIDENTIFIER: "identifier",
	FIELD_CONTRIBUTOR: "NONE",
	FIELD_CONTRIBUTORIDENTIFIER: "identifier",
	FIELD_CONTRIBUTORAFFILIATION: "affiliation",
	FIELD_CONTRIBUTORAFFILIATIONIDENTIFIER: "identifier",
	FIELD_PUBLISHER: "publisher",
	FIELD_PUBLISHERIDENTIFIER: "identifier",
	FIELD_RELATEDINSTRUMENTS: "relatedInstruments",
	FIELD_RELATEDINSTRUMENTIDENTIFIER: "identifier",
	FIELD_RELATEDOBSERVATORIES: "relatedObservatories",
	FIELD_SOFTWARENAME: "softwareName",
	FIELD_VERSIONNUMBER: "version",
	FIELD_VERSIONDATE: "release_date",
	FIELD_VERSIONDESCRIPTION: "description",
	FIELD_VERSIONPID: "version_pid",
	FIELD_REFERENCEPUBLICATION: "referencePublication",
	FIELD_DESCRIPTION: "description",
	FIELD_CONCISEDESCRIPTION: "conciseDescription",
	FIELD_SOFTWAREFUNCTIONALITY: "softwareFunctionality",
	FIELD_DOCUMENTATION: "documentation",
	FIELD_DATASOURCES: "dataSources",
	FIELD_INPUTFORMATS: "inputFormats",
	FIELD_OUTPUTFORMATS: "outputFormats",
	FIELD_RELATEDPUBLICATIONS: "relatedPublications",
	FIELD_RELATEDDATASETS: "relatedDatasets",
	FIELD_RELATEDDATASETNAME: "name",
	FIELD_DEVELOPMENTSTATUS: "developmentStatus",
	FIELD_OPERATINGSYSTEM: "operatingSystem",
	FIELD_CPUARCHITECTURE: "cpuArchitecture",
	FIELD_METADATALICENSE: "metadataLicense",
	FIELD_METADATALICENSEURI: "url",
	FIELD_METADATALICENSEIDENTIFIER: "NONE",
	FIELD_METADATALICENSEIDENTIFIERSCHEME: "NONE",
	FIELD_METADATASCHEMEURI: "NONE",
	FIELD_LICENSE: "license",
	FIELD_LICENSEURI: "url",
	FIELD_LICENSEFILEURL: "NONE",
	FIELD_LICENSEIDENTIFIER: "NONE",
	FIELD_LICENSEIDENTIFIERSCHEME: "NONE",
	FIELD_SCHEMEURI: "NONE",
	FIELD_RELATEDREGION: "relatedRegion",
	FIELD_KEYWORDS: "keywords",
	FIELD_RELATEDSOFTWARE: "relatedSoftware",
	FIELD_INTEROPERABLESOFTWARE: "interoperableSoftware",
	FIELD_FUNDER: "funder",
	FIELD_FUNDERIDENTIFIER: "identifier",
	FIELD_AWARDTITLE: "award",
	FIELD_AWARDNUMBER: "identifier",
	FIELD_CODEREPOSITORYURL: "codeRepositoryUrl",
	FIELD_LOGO: "logo",
	FIELD_RELATEDPHENOMENA: "relatedPhenomena",
	FIELD_SUBMITTERNAME: "submitter",
	FIELD_SUBMITTEREMAIL: "email",
	FIELD_CURATORNAME: "curator",
	FIELD_CURATOREMAIL: "email",
}