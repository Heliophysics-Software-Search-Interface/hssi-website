import {
	type JSONArray,
	type JSONObject
} from "./loader";

export interface ArrayData extends JSONObject {
	data: JSONArray,
}

export interface HSSIModelData extends JSONObject {
	/** string represinting a unique UUID for the object */
	id: string,
}

export interface ControlledListData extends HSSIModelData {
	/** string representing a human-readable display name */
	name: string,
	/** url identifier such as DOI, ROR, or ORCID */
	identifier: string,
}

export interface GraphListData extends ControlledListData {
	/** list of UUIDs pointing to nodes that are children of this object */
	children: JSONArray<string>,
	/** list of UUIDs pointing to nodes that are parents of this object */
	parents?: JSONArray<string>,
}

export interface KeywordData extends ControlledListData { }

export interface FunctionalityData extends GraphListData { 
	abbreviation?: string,
	backgroundColor: string,
	textColor: string,
}

export interface VersionData extends HSSIModelData {
	number: string,
}

export interface OrganizationData extends HSSIModelData {
	name: string,
	/** ROR identifier url of the organization */
	identifier?: string,
}

export interface PersonData extends HSSIModelData {
	firstName: string,
	lastName: string,
	/** ORCID of the person */
	identifier?: string,
	affiliations: JSONArray<OrganizationData>,
}

export interface SoftwareData extends HSSIModelData {
	programmingLanguage: JSONArray<ControlledListData>,
	publicationDate: string,
	publisher: OrganizationData,
	authors: JSONArray<PersonData>,
	relatedInstruments: JSONArray<ControlledListData>,
	relatedObservatories: JSONArray<ControlledListData>,
	softwareName: string,
	version: VersionData,
	persistentIdentifier: string,
	referencePublication: ControlledListData,
	description: string,
	conciseDescription: string,
	softwareFunctionality: string,
	documentation: string,
	dataSources: JSONArray<ControlledListData>,
	inputFormats: JSONArray<ControlledListData>,
	outputFormats: JSONArray<ControlledListData>,
	cpuArchitecture: JSONArray<ControlledListData>,
	relatedPublications: JSONArray<ControlledListData>,
	relatedDatasets: JSONArray<ControlledListData>,
	developmentStatus: ControlledListData,
	operatingSystem: JSONArray<ControlledListData>,
	license: JSONArray<ControlledListData>,
	relatedRegion: JSONArray<ControlledListData>,
	keywords: JSONArray<KeywordData>,
	relatedSoftware: JSONArray<ControlledListData>,
	interoperableSoftware: JSONArray<ControlledListData>,
	funder: OrganizationData,
	award: HSSIModelData,
	codeRepositoryUrl: string,
	logo: JSONObject,
	relatedPhenomena: JSONArray<ControlledListData>,
	submissionInfo: JSONObject,
}