# Submission REST API

To submit an item to HSSI through the REST API instead of using the submission 
form, follow the specification below.

## Example JSON

See [this JSON file](./import_submission.json) for an acceptable submission 
example of a single submission object.

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
	* subfields:
		* `email` *required* - email address
		* `person` *required* [`Person`](#person) object
			* subfields:
				* `firstName` *required*
				* `lastName` *required*
* `softwareName` *required*
* `codeRepositoryUrl` *required*
* `authors` *required* - array of [`Person`](#person) objects
	* subfields
		* `firstName` *required*
		* `lastName` *required*
* `description` *required*

### Recommended

These fields can be omitted, however, doing so will likely have a negative 
impact on the software's discoverability and usability.

* `documentation` - url
* `persistentIdentifier` - url
* `softwareFunctionality` - array of UUIDs
	* UUID strings must be taken from `id` field on items in:
	`/api/models/FunctionCategory/rows/all`
* `publicationDate` - date (ISO format string)
* `publisher` - [`Organization`](#organization) object
* `license` - license name string 
	* must be **exact match** taken from a `name` field in 
	[`/api/models/License/rows/all`](https://hssi.hsdcloud.org/api/models/License/rows/all/)
* `version` - object
	* subfields:
		* `number` - version number string, see https://semver.org/
		* `release_date` - date (ISO format string)
		* `description` - text
		* `version_pid` - url
* `relatedRegion` - array of region name strings
	* must be **exact match** taken from `name` field in
	[`/api/models/Region/rows/all/`](https://hssi.hsdcloud.org/api/models/Region/rows/all/)
* `programmingLanguage` - array of programming language name strings
	* must be **exact match** taken from `name` field in
	[`/api/models/ProgrammingLanguage/rows/all/`](https://hssi.hsdcloud.org/api/models/ProgrammingLanguage/rows/all/)
* `inputFormats` - array of file format strings
	* must be **exact match** taken from `name` field in
	[`/api/models/FileFormat/rows/all/`](https://hssi.hsdcloud.org/api/models/FileFormat/rows/all/)
* `outputFormats` - array of file format strings
	* must be **exact match** taken from `name` field in
	[`/api/models/FileFormat/rows/all/`](https://hssi.hsdcloud.org/api/models/FileFormat/rows/all/)
* `operatingSystem` - array of OS strings
	* must be **exact match** taken from `name` field in
	[`/api/models/OperatingSystem/rows/all/`](https://hssi.hsdcloud.org/api/models/OperatingSystem/rows/all/)
* `cpuArchitecture` - array of cpu architecture strings
	* must be **exact match** taken from `name` field in
	[`/api/models/CPUArchitecture/rows/all/`](https://hssi.hsdcloud.org/api/models/CPUArchitecture/rows/all/)
* `developmentStatus` - repo status string
	* must be **exact match** taken from `name` field in
	[`/api/models/RepoStatus/rows/all/`](https://hssi.hsdcloud.org/api/models/RepoStatus/rows/all/)

### Optional

These fields are helpful to have for discoverability and ease of access, 
however they may not be applicable to some submissions.

* `relatedInstruments` - array of [`Instrument`](#instrument) object
* `relatedObservatories` - array of [`Observatory`](#observatory) object
* `referencePublication` - url
* `conciseDescription` - text
	* must be 200 characters or less
* `dataSources` - array of data source strings
	* must be **exact match** from `name` field in
	[`/api/models/DataInput/rows/all/`](https://hssi.hsdcloud.org/api/models/DataInput/rows/all/)
* `relatedPublications` - array of urls
* `relatedDatasets` - array of urls
* `keywords` - array of strings
* `relatedSoftware` - array of urls
* `interoperableSoftware` - array of urls
* `funder` - [`Organization`](#organization) object
* `award` - array of objects
	* subfields:
		* `name` - string
		* `identifier` - string
* `logo` - url
* `relatedPhenomena` array of phenomena strings
	* must be **exact match** from `name` field in
	[`/api/models/Phenomena/rows/all/`](https://hssi.hsdcloud.org/api/models/Phenomena/rows/all/)

## Object Specifications

### Person
### Submitter
### Organization
### Function Category
### Instrument
### Award