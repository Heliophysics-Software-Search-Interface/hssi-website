/**
 * TypeScript types for the model names and JSON data shapes returned by the
 * backend model API. Touch this when a backend model or one of its serialized
 * fields is added or renamed.
 *
 * @module
 */

import {
	type JSONArray,
	type JSONObject
} from "../loader";

/**
 * Union of the backend model names that data can be fetched for, e.g.
 * `"Software"`, `"VerifiedSoftware"`, `"FunctionCategory"`, `"Person"`.
 */
export type ModelName = ( 
	"HSSIModel" 
	| "HssiSet" 
	| "ControlledList"
	| "ControlledGraphList"
	| "Keyword"
	| "OperatingSystem"
	| "CpuArchitecture"
	| "Phenomena"
	| "RepoStatus"
	| "Image"
	| "ProgrammingLanguage"
	| "DataInput"
	| "FileFormat"
	| "Region"
	| "InstrumentObservatory"
	| "FunctionCategory"
	| "License"
	| "Organization"
	| "Software"
	| "SoftwareVersion"
	| "VerifiedSoftware"
	| "SoftwareEditQueue"
	| "SubmissionInfo"
	| "Award"
	| "RelatedItem"
	| "Person"
	| "Submitter"
	| "Curator"
);

/** Base data for every model object: its UUID `id`. */
export interface HSSIModelData extends JSONObject {
	/** string represinting a unique UUID for the object */
	id: string,
}

/**
 * Controlled list term data: display `name` and URL `identifier` (DOI, ROR,
 * ORCID, etc.).
 */
export interface ControlledListData extends HSSIModelData {
	/** string representing a human-readable display name */
	name: string,
	/** url identifier such as DOI, ROR, or ORCID */
	identifier: string,
}

/**
 * Controlled list term data with `children` and optional `parents` UUID lists.
 */
export interface GraphListData extends ControlledListData {
	/** list of UUIDs pointing to nodes that are children of this object */
	children: JSONArray<string>,
	/** list of UUIDs pointing to nodes that are parents of this object */
	parents?: JSONArray<string>,
}

/** Keyword data; same shape as `ControlledListData`. */
export interface KeywordData extends ControlledListData { }

/**
 * Function category data: graph list data plus optional `abbreviation`,
 * `backgroundColor` and `textColor`.
 */
export interface FunctionalityData extends GraphListData {
	abbreviation?: string,
	backgroundColor: string,
	textColor: string,
}

/** Software version data: `number` and `release_date`. */
export interface VersionData extends HSSIModelData {
	number: string,
	release_date: string,
}

/** Organization data: `name` and optional ROR `identifier`. */
export interface OrganizationData extends HSSIModelData {
	name: string,
	/** ROR identifier url of the organization */
	identifier?: string,
}

/**
 * Person data: `given_name`, `family_name`, optional ORCID `identifier`, and
 * `affiliation` organizations.
 */
export interface PersonData extends HSSIModelData {
	given_name: string,
	family_name: string,
	/** ORCID of the person */
	identifier?: string,
	affiliation: JSONArray<OrganizationData>,
}

/**
 * Full software entry data with related objects nested as their data types,
 * plus an optional `metadata_modified_date` used for sorting.
 */
export interface SoftwareData extends HSSIModelData {
	programming_language: JSONArray<ControlledListData>,
	publication_date: string,
	metadata_modified_date?: string,
	publisher: OrganizationData,
	authors: JSONArray<PersonData>,
	related_instruments: JSONArray<ControlledListData>,
	related_observatories: JSONArray<ControlledListData>,
	software_name: string,
	version: VersionData,
	persistent_identifier: string,
	reference_publication: ControlledListData,
	description: string,
	concise_description: string,
	documentation: string,
	software_functionality: JSONArray<FunctionalityData>,
	data_sources: JSONArray<ControlledListData>,
	input_formats: JSONArray<ControlledListData>,
	output_formats: JSONArray<ControlledListData>,
	cpu_architecture: JSONArray<ControlledListData>,
	related_publications: JSONArray<ControlledListData>,
	related_datasets: JSONArray<ControlledListData>,
	development_status: ControlledListData,
	operating_system: JSONArray<ControlledListData>,
	license: JSONArray<ControlledListData>,
	related_region: JSONArray<ControlledListData>,
	keywords: JSONArray<KeywordData>,
	related_software: JSONArray<ControlledListData>,
	interoperable_software: JSONArray<ControlledListData>,
	funder: JSONArray<OrganizationData>,
	award: HSSIModelData,
	code_repository_url: string,
	logo: string,
	related_phenomena: JSONArray<ControlledListData>,
	submissionInfo: JSONObject,
	scix_url?: string,
}
