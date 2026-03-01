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
* `software_name` *required*
* `codeRepositoryUrl` *required*
* `authors` *required* - array of [`Person`](#person) objects
* `description` *required*

### Recommended

These fields can be omitted, however, doing so will likely have a negative 
impact on the software's discoverability and usability.

* `documentation` - url
* `persistent_identifier` - url
* `software_functionality` - array of full names
	* full names should be formated as `Parent Name: Child Name`, where parent
	and child names must be **exact matches** taken from `name` field in
	[`/api/models/FunctionCategory/rows/all`](https://hssi.hsdcloud.org/api/models/FunctionCategory/rows/all/)
* `publication_date` - date (ISO format string)
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
* `programming_language` - array of programming language name strings
	* must be **exact match** taken from `name` field in
	[`/api/models/ProgrammingLanguage/rows/all/`](https://hssi.hsdcloud.org/api/models/ProgrammingLanguage/rows/all/)
* `input_formats` - array of file format strings
	* must be **exact match** taken from `name` field in
	[`/api/models/FileFormat/rows/all/`](https://hssi.hsdcloud.org/api/models/FileFormat/rows/all/)
* `output_formats` - array of file format strings
	* must be **exact match** taken from `name` field in
	[`/api/models/FileFormat/rows/all/`](https://hssi.hsdcloud.org/api/models/FileFormat/rows/all/)
* `operating_system` - array of OS strings
	* must be **exact match** taken from `name` field in
	[`/api/models/OperatingSystem/rows/all/`](https://hssi.hsdcloud.org/api/models/OperatingSystem/rows/all/)
* `cpu_architecture` - array of cpu architecture strings
	* must be **exact match** taken from `name` field in
	[`/api/models/CPUArchitecture/rows/all/`](https://hssi.hsdcloud.org/api/models/CPUArchitecture/rows/all/)
* `development_status` - repo status string
	* must be **exact match** taken from `name` field in
	[`/api/models/RepoStatus/rows/all/`](https://hssi.hsdcloud.org/api/models/RepoStatus/rows/all/)

### Optional

These fields are helpful to have for discoverability and ease of access, 
however they may not be applicable to some submissions.

* `related_instruments` - array of [`Instrument`](#instrument) object
* `related_observatories` - array of [`Observatory`](#observatory) object
* `reference_publication` - url
* `concise_description` - text
	* must be 200 characters or less
* `data_sources` - array of data source strings
	* must be **exact match** from `name` field in
	[`/api/models/DataInput/rows/all/`](https://hssi.hsdcloud.org/api/models/DataInput/rows/all/)
* `related_publications` - array of urls
* `related_datasets` - array of urls
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

Object fields will not duplicate if a match is found, each object type has 
different matching criteria specified below. If a match is not found, a new
entry to the proper database field is defined. If an a match is found and 
it has less fields filled out, the match will be updated in the database with 
the new information. If a match is found and it has conflicting fields, the
information from the fields already in the database will be used, and new 
information will be ignored.

### Person

References `Person` table in database, hard match on `identifier`,
otherwise fall back to matching on a combination of `given_name` + `family_name`

#### Subfields

* `firstname` *required* - string
* `lastname` *required* - string
* `identifier` - url
* `affiliation` - array of [`Organization`](#organization) objects

### Submitter

References `Submitter` table in database, hard match on `email`

#### Subfields

* `email` *required* - string
* `person` *required* - [`Person`](#person) object

### Organization

References `Organization` table in database, hard match on `identifier`

#### subfields

* `name` *required* - string
* `abbreviation` - string
* `identifier` - url

### Observatory

Same as [`Instrument`](#instrument), but handled differently in different 
submission fields

### Instrument

References `InstrumentObservatory` table in database, hard match on `identifier`

#### subfields
* `name` *required* - url
* `abbrevieation` *required* - url
* `definition` - text