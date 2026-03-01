import { 
	FormGenerator,
	type JSONObject,
	type NestedKeys 
} from "../loader";

/** data that represents all fields in the software submission form */
export type SubmissionFormData = {
	submitterName?: string,
	persistent_identifier?: string,
	codeRepositoryURL?: string,
	authors?: {
		authors?: string,
		authorIdentifier?: string,
		authorAffiliation?: {
			authorAffiliation?: string,
			authorAffiliationIdentifier?: string,
		}[],
	}[],
	software_name?: string,
	description?: string,
	concise_description?: string,
	publication_date?: string,
	publisher?: {
		publisher?: string,
		publisherIdentifier?: string,
	},
	versionNumber?: {
		versionNumber?: string,
		versionDate?: string,
		versionDescription?: string,
		versionPID?: string,
	},
	programming_language?: string[],
	license?: {
		license?: string,
		licenseURI?: string,
	},
	keywords?: string[],
	software_functionality?: string[],
	data_sources?: string[],
	inputFormats?: string[],
	outputFormats?: string[],
	operatingSystem?: string[],
	cpuArchitecture?: string[],
	relatedRegion?: string[],
	reference_publication?: string,
	developmentStatus?: string,
	documentation?: string,
	funder?: {
		funder?: string,
		funderIdentifier?: string,
	}[],
	awardTitle?: {
		awardTitle?: string,
		awardNumber?: string,
	}[],
	relatedPublications?: string[],
	relatedDatasets?: string[],
	relatedSoftware?: string[],
	interoperableSoftware?: string[],
	related_instruments?: {
		related_instruments?: string,
		relatedInstrumentIdentifier?: string,
	}[],
	related_observatories?: {
		related_observatories?: string,
		relatedObservatoryIdentifier?: string,
	}[],
	logo?: string,
}

enum ModelUpdateMethod {
	pickExistingEntry,
	updateExistingEntry,
	addNewEntry,
}

type ModelName = (
	"Keyword" |
	"OperatingSystem" |
	"Phenomena" |
	"RepoStatus" |
	"Image" |
	"ProgrammingLanguage" |
	"DataInput" |
	"FileFormat" |
	"Region" |
	"InstrumentObservatory" |
	"FunctionCategory" |
	"License" |
	"Organization" |
	"Person" |
	"Submitter" |
	"Award" |
	"RelatedItem" |
	"SoftwareVersion" |
	"Software"
);

export class FormSubmission {
	private formData: SubmissionFormData = null;

	private submit(): void {
		const structures = FormGenerator.getStructureData();
		const Software: JSONObject = {}
	}
}