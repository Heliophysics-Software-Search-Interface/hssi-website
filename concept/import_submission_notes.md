# Submission REST API

To submit an item to HSSI through the REST API instead of using the submission 
form, follow the specification below.

## Example JSON

See [this JSON file](./import_submission.json) for an acceptable submission 
example of a single submission object. The fields in the example are listed 
alphabetically. The same fields are listed in useful categories with the 
examples copied below. Recommended and optional fields with subcomponents
(e.g., funder) do not need to be completely filled to be accepted. In these 
cases, the preference is to have correct identifiers if other subcomponent 
fields are not included.

## Endpoint

Send a `POST` request to `*domain*/api/submit`, the `POST` should contain `JSON` 
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
valid, and will not be accepted.

* `submitter` *required* - array of [`Submitter`](#submitter) objects
	```
	"submitter": [
		{
			"email": "example@email.org",
			"person": {
				"firstName": "Isaiah",  
				"lastName": "Smith",
				"identifier": "https://orcid.org/0000-0002-1825-0097"  
			}
		}
	],
	```
* `softwareName` *required*
	```
	"softwareName": "Example Name",	
	```
* `codeRepositoryUrl` *required*
	```
	"codeRepositoryUrl": "https://repo.example.org/example",
	```
* `authors` *required* - array of [`Person`](#person) objects
	```
	"authors": [
		{
			"firstName": "Isaiah",  
			"lastName": "Smith",
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
		},
		{
			"firstName": "Shawn",  
			"lastName": "Polson",
			"identifier": "https://orcid.org/0000-0003-0619-5745"
		}
	],
	```
* `description` *required*
	```
	"description": "This software does ALL the things, it is the BEST software EVER.",	
	```
### Recommended

These fields can be omitted, however, doing so will likely have a negative 
impact on the software's discoverability and usability.

* `documentation` - url
	```
	"documentation": "https://docs.example.org/heliospectra",
	```
* `persistentIdentifier` - url
	```
	"persistentIdentifier": "https://doi.org/10.XXXX/conceptDOIexample",
	```
* `softwareFunctionality` - array of terms.
   * must be an **exact match** taken from [`/api/models/Functionality/rows/all`](https://hssi.hsdcloud.org/api/models/Functionality/rows/all/)  **please correct this link**
	```
	"softwareFunctionality": [
		"Data Processing and Analysis",
		"Data Processing and Analysis: Energy Spectra"
	],	
	```
* `publicationDate` - date (ISO format string)
	```
	"publicationDate": "2024-06-14",
	```
* `publisher` - [`Organization`](#organization) object
	```
	"publisher": {
		"name": "Example Publisher",
		"identifier": "https://ror.org/012345678"
	},	
	```
* `license` - license name string 
	* must be **exact match** taken from a `name` field in 
	[`/api/models/License/rows/all`](https://hssi.hsdcloud.org/api/models/License/rows/all/)
	* license URLs can be retrieved from the [list](https://spdx.org/licenses/) on SPDX.
	```
	"license": {
		"name": "GNU Library or 'Lesser' General Public Licenses (LGPL version 3)",
		"url": "https://spdx.org/licenses/LGPL-3.0-or-later"
	},
	```
* `version` - object
	* subfields:
		* `number` - version number string, see https://semver.org/
		* `releaseDate` - date (ISO format string)
		* `description` - text
		* `versionPID` - url
	```
	"version": {
		"number": "2.4.1",
		"versionDate": "2025-05-01",
		"description": "Adds adaptive deconvolution and GPU acceleration.",
		"versionPID": "https://doi.org/10.XXXX/example"
	}		
	```
* `relatedRegion` - array of region name strings
	* must be **exact match** taken from `name` field in
	[`/api/models/Region/rows/all/`](https://hssi.hsdcloud.org/api/models/Region/rows/all/)
    * In the future, these must match one of the region names found in the selected list. This will be supported by an API for search and matching.
	```
	"relatedRegion": [
		"Solar Environment",
		"Interplanetary Space"
	],
	```
* `programmingLanguage` - array of programming language name strings
	* must be **exact match** taken from `name` field in
	[`/api/models/ProgrammingLanguage/rows/all/`](https://hssi.hsdcloud.org/api/models/ProgrammingLanguage/rows/all/)
	```
	"programmingLanguage": [
		"Python 3.x",
		"Fortran 2003"
	],
	```
* `inputFormats` - array of file format strings
	* must be **exact match** taken from `name` field in
	[`/api/models/FileFormat/rows/all/`](https://hssi.hsdcloud.org/api/models/FileFormat/rows/all/)
	```
	"inputFormats": [
		"CDF",
		"FITS"
	],	
	```
* `outputFormats` - array of file format strings
	* must be **exact match** taken from `name` field in
	[`/api/models/FileFormat/rows/all/`](https://hssi.hsdcloud.org/api/models/FileFormat/rows/all/)
	```
	"outputFormats": [
		"CDF",
		"FITS"
	],	
	```
* `operatingSystem` - array of OS strings
	* must be **exact match** taken from `name` field in
	[`/api/models/OperatingSystem/rows/all/`](https://hssi.hsdcloud.org/api/models/OperatingSystem/rows/all/)
	```
	"operatingSystem": [
		"Linux",
		"Mac"
	],
	```
* `cpuArchitecture` - array of cpu architecture strings
	* must be **exact match** taken from `name` field in
	[`/api/models/CPUArchitecture/rows/all/`](https://hssi.hsdcloud.org/api/models/CPUArchitecture/rows/all/)
	```
	"cpuArchitecture": [
		"x86-64",
		"Apple Silicon arm64"
	],	
	```
* `developmentStatus` - repo status string
	* must be **exact match** taken from `name` field in
	[`/api/models/RepoStatus/rows/all/`](https://hssi.hsdcloud.org/api/models/RepoStatus/rows/all/). Only one value is allowed.
	* More information on what each term means can be obtained from [https://www.repostatus.org/](https://www.repostatus.org/).
	```
	"developmentStatus": "Active",
	```

### Optional

These fields are helpful to have for discoverability and ease of access, 
however they may not be applicable to some submissions.

* `relatedInstruments` - array of [`Instrument`](#instrument) object
    * In the future, these must match one of the instrument names found in SPASE. This will be supported by an API for search and matching.
	```
	"relatedInstruments": [
		{
			"name": "Visible Spectro-Polarimeter",
		},
		{
			"name": "Atmospheric Imaging Assembly",
			"identifier": "https://doi.org/10.XXXX/example"
		}
	],	
	```
* `relatedObservatories` - array of [`Observatory`](#observatory) object
  * In the future, these must match one of the observatory names found in SPASE. This will be supported by an API for search and matching.
	```
	"relatedObservatories": [
		{
			"name": "Solar Orbiter",
			"identifier": "https://doi.org/10.XXXX/example"
		},
		{
			"name": "Daniel K. Inouye Solar Telescope",
			"definition": "A ground-based solar telescope."
		}
	],	
	```
* `referencePublication` - DOI url
	```
	"referencePublication": "https://doi.org/10.XXXX/example",
	```
* `conciseDescription` - text
	* must be 200 characters or less
	```
	"conciseDescription": "Good software install now",
	```
* `dataSources` - array of data source strings
	* must be **exact match** from `name` field in
	[`/api/models/DataInput/rows/all/`](https://hssi.hsdcloud.org/api/models/DataInput/rows/all/)
	```
	"dataSources": [
		"CDAWeb",
		"HAPI"
	],
	```
* `relatedPublications` - array of DOI urls
	```
	"relatedPublications": [
		"https://doi.org/10.XXXX/example",
		"https://doi.org/10.XXXX/example"
	],
	```
* `relatedDatasets` - array of urls, preferably DOIs
	```
	"relatedDatasets": [
		"https://doi.org/10.XXXX/example",
		"https://doi.org/10.XXXX/example"
	],
	```
* `keywords` - array of strings
	```
	"keywords": [
		"spectroscopy",
		"magnetic fields"
	],	
	```
* `relatedSoftware` - array of urls, preferable concept DOIs
	```
	"relatedSoftware": [
		"https://doi.org/10.XXXX/example",
		"https://doi.org/10.XXXX/example"
	],
	```
* `interoperableSoftware` - array of urls, preferably concept DOIs
	```
	"interoperableSoftware": [
		"https://doi.org/10.XXXX/example",
		"https://doi.org/10.XXXX/example"
	],	
	```
* `funder` - [`Organization`](#organization) object
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
* `award` - array of objects
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
* `logo` - url
	```
	"logo": "https://cdn.example.org/heliospectra/logo.png",
	```
* `relatedPhenomena` array of phenomena strings
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

References `Person` table in database, hard match on `identifier`,
otherwise fall back to matching on a combination of `firstName` + `lastName`

#### Subfields

* `firstname` *required* - string
* `lastname` *required* - string
* `identifier` - url
* `affiliation` - array of [`Organization`](#organization) objects

### Submitter

References `Submitter` table in database, hard match on `identifier`

#### Subfields

* `email` *required* - string
* `person` *required* - [`Person`](#person) object
* `identifier` - url

### Organization

References `Organization` table in database, hard match on `identifier`

#### subfields

* `name` *required* - string
* `identifier` - url

### Observatory

Same as [`Instrument`](#instrument), but handled differently in different 
submission fields

### Instrument

References `InstrumentObservatory` table in database, hard match on `identifier`

#### subfields
* `name` *required* - text
* `identifier` - url
