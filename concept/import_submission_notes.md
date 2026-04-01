# Submission REST API

To submit an item to HSSI through the REST API instead of using the submission 
form, follow the specification below.

## Example JSON

See [this JSON file](./import_submission.json) for a complete submission 
example of a single submission object. The fields in the example are listed 
alphabetically. The same fields are listed in useful categories with the 
examples copied below. Recommended and optional fields with subcomponents
(e.g., funder) do not need to be completely filled to be accepted. In these 
cases, the preference is to have correct identifiers if other subcomponent 
fields are not included.

## Endpoint

Send a `POST` request to `*domain*/api/submission`, the `POST` should contain `JSON` 
formatted body text. The root level object **must be an array**, and each item
object in the root level array will be a separate submission.

Example:
```
[
	{
		... submission 1 ...
	},
	{
		... submission 2 ...
	}
]
```


## Fields

### Required

These fields **must be in the json object**, otherwise the submission is not 
valid, and will not be accepted. Additional components of the example below 
are possible but not required. See [this JSON file](./import_submission.json) 
for a complete example.

* `submitter` *required* - array of [`Submitter`](#submitter) objects. The
  submitter's name and email are required.
	```
	"submitter": [
		{
			"email": "example@email.org",
			"person": {
				"givenName": "Isaiah",  
				"familyName": "Smith"
			}
		}
	],
	```
* `softwareName` *required*. The name of the software or service.
	```
	"softwareName": "Example Name",	
	```
* `codeRepositoryUrl` *required*. The link where the uncompiled human-readable
  code can be viewed or where access to the code can be requested.
	```
	"codeRepositoryUrl": "https://repo.example.org/example",
	```
* `authors` *required* - array of [`Person`](#person) objects. The names of 
  all authors of this software.
	```
	"authors": [
		{
			"givenName": "Isaiah",  
			"familyName": "Smith"
		},
		{
			"givenName": "Shawn",  
			"familyName": "Polson"
		}
	],
	```
* `description` *required*. A useful description of the software. The first
  150-200 characters will be used as the preview.
	```
	"description": "This software does ALL the things, it is the BEST software EVER.",	
	```

### Recommended

These fields can be omitted, however, doing so will likely have a negative 
impact on the software's discoverability and usability.

* `submitterIdentifier`  - The ORCiD link of the person submitting the resource. To be
  added to the submitter object as shown below.
	```
	"submitter": [
		{
			"email": "example@email.org",
			"person": {
				"givenName": "Isaiah", 
				"familyName": "Smith",
				"identifier": "https://orcid.org/0000-0002-1825-0097"
			}
		}
	],	
	```
* `authorAffiliation` - Name of the author's affiliation -
  and `Identifier` - the ORCiD link (person) or ROR link (organization) appropriate for the author. 
  To be added to the authors object as shown below.
	```
	"authors": [
	{
		"givenName": "Isaiah",
		"familyName": "Smith",
		"identifier": "https://orcid.org/0009-0001-1713-2830",
		"affiliation": [
			{
				"name": "Laboratory for Atmospheric and Space Physics"
			},
			{
				"name": "University of Colorado Boulder"
			}
		]
	},
	```
* `documentation` - url. Link to the documentation and installation instructions.
  If this is the same as the access URL, then enter that link here.
	```
	"documentation": "https://docs.example.org/heliospectra",
	```
* `persistentIdentifier` - url. The globally unique persistent identifier for
  the software (e.g. the concept DOI for all versions).
	```
	"persistentIdentifier": "https://doi.org/10.XXXX/conceptDOIexample",
	```
* `softwareFunctionality` - array of terms. All of the relevant software
  functionalities that apply. More is better here to aid in discovery.
   * must be an **exact match** taken from [`/api/models/Functionality/rows/all`](https://hssi.hsdcloud.org/api/models/Functionality/rows/all/)  **please correct this link**
	```
	"softwareFunctionality": [
		"Data Processing and Analysis",
		"Data Processing and Analysis: Energy Spectra"
	],	
	```
* `publicationDate` - date (ISO format string). The date the software
  was published or the date the DOI was assigned.
	```
	"publicationDate": "2024-06-14",
	```
* `publisher` - [`Organization`](#organization) object. The name of the
  publisher (e.g., Zenodo).
	```
	"publisher": {
		"name": "Example Publisher"
	},	
	```
* `license` - license name string. The full name of the license assigned
  to this software from the list indicated. If the software is restricted,
  please enter "Restricted" into this field without the quotes. 
	* must be **exact match** taken from a `name` field in 
	[`/api/models/License/rows/all`](https://hssi.hsdcloud.org/api/models/License/rows/all/)
	* license URLs can be retrieved from the [list](https://spdx.org/licenses/) on SPDX.
	```
	"license": "BSD 3-Clause \"New\" or \"Revised\" License",
	```
* `version` - object. The version number is the most recent major
  version of the software. The version date is publication date of the
  indicated version of the software. The version description is a
  description of the changes between the last major release and this
  release. The version PID is the globally unique persistent identifier
  for the specific version of the software (e.g., DOI for the version).
	* subfields:
		* `number` - version string, see https://semver.org/
		* `versionDate` - date (ISO format string)
		* `description` - text
		* `versionPid` - url
	```
	"version": {
		"number": "2.4.1",
		"versionDate": "2025-05-01",
		"description": "Adds adaptive deconvolution and GPU acceleration.",
		"versionPID": "https://doi.org/10.XXXX/example"
	}		
	```
* `relatedRegion` - array of region name strings. The physical region the
  software supports science or operational functionality for. 
	* These must be an exact match to one of region names used by HelioData. This is supported by an API for search and matching. See [https://api.heliophysics.net/api/regions/](https://api.heliophysics.net/api/regions/) for more information. 
	```
	"relatedRegion": [
		"Solar Environment",
		"Interplanetary Space"
	],
	```
* `programmingLanguage` - array of programming language name strings.
  The computer programming languages most important for the software.
	* must be **exact match** taken from `name` field in
	[`/api/models/ProgrammingLanguage/rows/all/`](https://hssi.hsdcloud.org/api/models/ProgrammingLanguage/rows/all/)
	```
	"programmingLanguage": [
		"Python 3.x",
		"Fortran 2003"
	],
	```
* `inputFormats` - array of file format strings.
  The file formats the software supports for data input.
	* must be **exact match** taken from `name` field in
	[`/api/models/FileFormat/rows/all/`](https://hssi.hsdcloud.org/api/models/FileFormat/rows/all/)
	```
	"inputFormats": [
		"CDF",
		"FITS"
	],	
	```
* `outputFormats` - array of file format strings.
  The file formats the software supports for data output.
	* must be **exact match** taken from `name` field in
	[`/api/models/FileFormat/rows/all/`](https://hssi.hsdcloud.org/api/models/FileFormat/rows/all/)
	```
	"outputFormats": [
		"CDF",
		"FITS"
	],	
	```
* `operatingSystem` - array of OS strings.
  The operating systems the software supports.
	* must be **exact match** taken from `name` field in
	[`/api/models/OperatingSystem/rows/all/`](https://hssi.hsdcloud.org/api/models/OperatingSystem/rows/all/)
	```
	"operatingSystem": [
		"Linux",
		"Mac"
	],
	```
* `cpuArchitecture` - array of cpu architecture strings.
  The CPU architecture the software requires.
	* must be **exact match** taken from `name` field in
	[`/api/models/CPUArchitecture/rows/all/`](https://hssi.hsdcloud.org/api/models/CPUArchitecture/rows/all/)
	```
	"cpuArchitecture": [
		"x86-64",
		"Apple Silicon arm64"
	],	
	```
* `developmentStatus` - repo status string.
  The development status of the software.
	* must be **exact match** taken from `name` field in
	[`/api/models/RepoStatus/rows/all/`](https://hssi.hsdcloud.org/api/models/RepoStatus/rows/all/). Only one value is allowed.
	* More information on what each term means can be obtained from [https://www.repostatus.org/](https://www.repostatus.org/).
	```
	"developmentStatus": "Active",
	```

### Optional

These fields are helpful to have for discoverability and ease of access, 
however they may not be applicable to some submissions.

* `affiliationIdentifier` - The identifier of the affiliation entity,
  such as the ROR, if one exists. This is to be added to the author
  object as shown below.
	```
	"authors": [
	{
		"givenName": "Isaiah",
		"familyName": "Smith",
		"identifier": "https://orcid.org/0009-0001-1713-2830",
		"affiliation": [
			{
				"name": "Laboratory for Atmospheric and Space Physics",
				"identifier": "https://ror.org/01fcjzv38"
			},
			{
				"name": "University of Colorado Boulder",
				"identifier": "https://ror.org/02ttsq026"
			}
		]
	}],
	```
* `publisherIdentifier` - The identifier of the publisher,
  such as the ROR. Note that Zenodo does not have an ROR,
  so the URL should be included instead. 
	```
	"publisher": {
		"name": "Example Publisher",
		"identifier": "https://ror.org/012345678"
	},	
	```
* `relatedInstruments` - array of [`Instrument`](#instrument) object
    * These should match one of the instrument names found in SPASE. This is supported by an API for search and matching. See [https://api.heliophysics.net/api/instruments/](https://api.heliophysics.net/api/instruments/). If no match is found in SPASE,
please add a URL or DOI for the instrument to help our users.
	```
	"relatedInstruments": [
		{
			"name": "Visible Spectro-Polarimeter"
		},
		{
			"name": "Atmospheric Imaging Assembly",
 			"identifier": "https://examplelink.com"
		}
	],	
	```
* `relatedObservatories` - array of [`Observatory`](#observatory) object.
  The mission or observatory the software is designed to support.
	*  These should match one of the observatory names found in SPASE. This is supported by an API for search and matching. See [[https://api.heliophysics.net/api/obseratory/](https://api.heliophysics.net/api/observatories/). If no match is found in SPASE,
please add a URL or DOI for the observatory to help our users.
	```
	"relatedObservatories": [
		{
			"name": "Solar Orbiter"
		},
		{
			"name": "Daniel K. Inouye Solar Telescope",
 			"identifier": "https://observatorywebsite.com"
		}
	],	
	```
* `referencePublication` - DOI url. The DOI for the publication
  describing the software, sometimes used as the preferred citation for
  the software in addition to the version-specific citation to the code
  itself.
	```
	"referencePublication": "https://doi.org/10.XXXX/example",
	```
* `conciseDescription` - text. A description of the item limited to
  150-200 characters. If the first 150-200 characters of the description
  do not provide the desired preview, you may enter an alternate text here.
	* must be 200 characters or less
	```
	"conciseDescription": "Good software install now",
	```
* `dataSources` - array of data source strings. The data input source the
  software supports.
	* must be **exact match** from `name` field in
	[`/api/models/DataInput/rows/all/`](https://hssi.hsdcloud.org/api/models/DataInput/rows/all/)
	```
	"dataSources": [
		"CDAWeb",
		"HAPI"
	],
	```
* `relatedPublications` - array of DOI urls. Publications that describe,
  cite, or use the software that the software developer prioritizes but
  are different from the reference publication.
	```
	"relatedPublications": [
		"https://doi.org/10.XXXX/example",
		"https://doi.org/10.XXXX/example"
	],
	```
* `relatedDatasets` - array of urls, preferably DOIs. Datasets the
  software supports functionality for (e.g. analysis).
	```
	"relatedDatasets": [
		"https://doi.org/10.XXXX/example",
		"https://doi.org/10.XXXX/example"
	],
	```
* `keywords` - array of strings. General science keywords relevant
  for the software (e.g. from the [UAT](https://astrothesaurus.org/concept-select/)) not supported by other
  metadata fields.
	```
	"keywords": [
		"spectroscopy",
		"magnetic fields"
	],	
	```
* `relatedSoftware` - array of urls, preferably concept DOIs.
  Software that performs similar tasks but does not necessarily
  link together (which would be considered interoperable software).
  For example, two software that model the upper atmosphere of
  Earth but use different assumption. 
	```
	"relatedSoftware": [
		"https://doi.org/10.XXXX/example",
		"https://doi.org/10.XXXX/example"
	],
	```
* `interoperableSoftware` - array of urls, preferably concept DOIs.
  Other important software packages this software has demonstrated
  interoperability with, such as being used with other software for
  a given task in some way.
	```
	"interoperableSoftware": [
		"https://doi.org/10.XXXX/example",
		"https://doi.org/10.XXXX/example"
	],	
	```
* `funder` - [`Organization`](#organization) object. The name of the
  organization that supports (sponsors) the software through some
  kind of financial contribution, and the globally unique persistent
  identifier for the funder (e.g., the ROR or DOI).
	```
	"funder": [
		{
			"name": "National Science Foundation",
			"identifier": "https://ror.org/021nxhr62"
		},
		{
			"name": "NASA Heliophysics Division",
			"identifier": "https://ror.org/03myraf72"
		}
	],	
	```
* `award` - array of objects. The award name is the title of the
  specific grant or award that funded the work, and the identifier
  is the award number or DOI of the award.
	* subfields:
		* `name` - string
		* `identifier` - string
	```
	"award": [
		{
			"name": "Example Award",
			"identifier": "NNG19PQ28C"
		},
		{
			"name": "Second Example Award",
			"identifier": "NNG19PB28C"
		}
	],	
	```
* `logo` - url. A link to the logo for the software.
	```
	"logo": "https://cdn.example.org/heliospectra/logo.png",
	```
* `relatedPhenomena` array of phenomena strings. The phenomena
  the software supports science or operational functionality for.
     * In the future, these must match one of the phenomena names found in the selected list. This will be supported by an API for search and matching.
	```
	"relatedPhenomena": [
		"Coronal Heating",
		"Geomagnetic Storms"
	],	
	```

## Object Specifications

Object fields will not duplicate if a match is found, each object type has 
different matching criteria specified below. If a match is not found, a new
entry to the proper database field is defined. If a match is found and 
it has less fields filled out, the match will be updated in the database with 
the new information. If a match is found and it has conflicting fields, the
information from the fields already in the database will be used, and new 
information will be ignored.

### Person

References `Person` table in database, hard match on `identifier` if provided,
otherwise fall back to matching on a combination of `givenName` + `familyName`

### Submitter

References `Submitter` table in database, hard match on `email`

### Organization

References `Organization` table in database, hard match on `identifier`, soft
match on `name` if identifier is not provided

### Instruments and Observatories

References `InstrumentObservatory` table in database, hard match on `identifier`.
the identifier is sourced from SPASE if a match is found.
