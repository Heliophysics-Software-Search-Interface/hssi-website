import { 
	type ModelName, 
	type JSONObject,
	type JSONArray,
	type HSSIModelData,
	type ControlledListData,
	type VersionData,
	type KeywordData,
	type FunctionalityData,
	fetchTimeout,
	isUuid4,
	type OrganizationData,
	type SoftwareData,
	type PersonData,
	ModelDataCache,
} from "../loader";

export const apiModel = "/api/models/";
export const apiSlugRowsAll = "/rows/all/";

export interface HssiDataAsync<T extends HSSIModelData> {
	get id(): string;
	get model(): ModelName;
	get hasData(): boolean;
	get loadedData(): T;
	getData(): Promise<T>;
}

export class HssiModelDataAsync<T extends HSSIModelData> 
	implements HSSIModelData, HssiDataAsync<T> 
{
	private objId: string = null;
	private modelData: T = null;

	/** the model (databse table) that the data will be fetched from */
	public model: ModelName = null;

	/** the uuid of the model object whose data should be fetched */
	public get id(): string { return this.objId; }

	/**
	 * model object data, only fetched if requested
	 * NOTE - the data type is ultimately determined by the {@link model},
	 * it is generic here to make it more convenient for manual typing
	 */
	protected get data(): T { return this.modelData; }

	/** returns the data if it's loaded but doesn't load it if it isn't */
	public get loadedData(): T { return this.data; }

	/** whether or not the data for the object has been loaded yet */
	public get hasData(): boolean { return !!this.data; }
	
	public constructor(model: ModelName, id: string){
		this.model = model;
		this.objId = id;
	}

	public setData(data: JSONObject) {
		// TODO set modelData to each key in data
		console.error("Not Implemented!");
	}

	/**
	 * returns the hssi model object data if it is available, otherwise 
	 * asynchronously fetches it, then returns it when it is done
	 */
	public async getData(): Promise<T>{
		return ModelDataCache.getModelData(this.model, this.id) as any;
	}
}

export interface PersonDataAsync extends HSSIModelData {
	given_name: string,
	family_name: string,
	/** ORCID of the person */
	identifier?: string,
	affiliation: Array<HssiDataAsync<OrganizationData>>,
}

export interface SoftwareDataAsync extends HSSIModelData {
	programming_language: Array<HssiDataAsync<ControlledListData>>,
	publication_date: string,
	publisher: HssiDataAsync<OrganizationData>,
	authors: Array<HssiDataAsync<PersonDataAsync>>,
	related_instruments: Array<HssiDataAsync<ControlledListData>>,
	related_observatories: Array<HssiDataAsync<ControlledListData>>,
	software_name: string,
	version: HssiDataAsync<VersionData>,
	persistent_identifier: string,
	reference_publication: HssiDataAsync<ControlledListData>,
	description: string,
	concise_description: string,
	documentation: string,
	software_functionality: Array<HssiDataAsync<FunctionalityData>>,
	data_sources: Array<HssiDataAsync<ControlledListData>>,
	input_formats: Array<HssiDataAsync<ControlledListData>>,
	output_formats: Array<HssiDataAsync<ControlledListData>>,
	cpu_architecture: Array<HssiDataAsync<ControlledListData>>,
	related_publications: Array<HssiDataAsync<ControlledListData>>,
	related_datasets: Array<HssiDataAsync<ControlledListData>>,
	development_status: HssiDataAsync<ControlledListData>,
	operating_system: Array<HssiDataAsync<ControlledListData>>,
	license: Array<HssiDataAsync<ControlledListData>>,
	keywords: Array<KeywordData>,
	related_software: Array<HssiDataAsync<ControlledListData>>,
	interoperable_software: Array<HssiDataAsync<ControlledListData>>,
	funder: Array<HssiDataAsync<OrganizationData>>,
	award: HssiDataAsync<HSSIModelData>,
	code_repository_url: string,
	logo: string,
	related_region: Array<HssiDataAsync<ControlledListData>>,
	related_phenomena: Array<HssiDataAsync<ControlledListData>>,
	submissionInfo: HssiDataAsync<HSSIModelData>,
}

// -----------------------------------------------------------------------------

function asyncifyUid<T extends HSSIModelData>(
	obj: JSONObject | string,
	targetModel: ModelName,
): HssiDataAsync<T> {
	let id = obj;
	if((obj as any)?.id) id = (obj as any).id;
	const r = new HssiModelDataAsync<T>(targetModel, id as string);

	// if it has more than "id" key, use the data in the object
	if(obj instanceof Object) for(const key in obj){
		if(key == "id") continue;
		if(!r.hasData) r.setData(obj);
		break;
	}

	return r;
}

function asyncifyJsonArray<T extends HSSIModelData>(
	arr: JSONArray<JSONObject | string>,
	targetModel: ModelName,
): Array<HssiDataAsync<T>> {
	const r: Array<HssiDataAsync<T>> = [];
	for(const obj of arr) {
		let asyncObj = obj;
		if(!(obj instanceof HssiModelDataAsync)) {
			asyncObj = asyncifyUid(asyncObj, targetModel);
		}
		r.push(asyncObj as any);
	}
	return r;
}

function asyncify<T extends HSSIModelData>(
	obj: JSONArray | JSONObject | string, 
	targetModel: ModelName
): Array<HssiDataAsync<T>> | HssiDataAsync<T> {
	if(obj == null) return null;
	if(obj instanceof Array) return asyncifyJsonArray<T>(obj, targetModel);
	else return asyncifyUid<T>(obj, targetModel);
}

export function createAsyncSoftwareData(data: SoftwareData): SoftwareDataAsync{
	return {
		id: data.id,
		programming_language: asyncify(data.programming_language, "ProgrammingLanguage") as any,
		publication_date: data.publication_date,
		publisher: asyncify(data.publisher, "Organization") as any,
		authors: asyncify(data.authors, "Person") as any,
		related_instruments: asyncify(data.related_instruments, "InstrumentObservatory") as any,
		related_observatories: asyncify(data.related_observatories, "InstrumentObservatory") as any,
		software_name: data.software_name,
		version: asyncify(data.version, "SoftwareVersion") as any,
		persistent_identifier: data.persistent_identifier,
		reference_publication: asyncify(data.reference_publication, "RelatedItem") as any,
		description: data.description,
		concise_description: data.concise_description,
		documentation: data.documentation,
		software_functionality: asyncify(data.software_functionality, "FunctionCategory") as any,
		data_sources: asyncify(data.data_sources, "DataInput") as any,
		input_formats: asyncify(data.input_formats, "FileFormat") as any,
		output_formats: asyncify(data.output_formats, "FileFormat") as any,
		cpu_architecture: asyncify(data.cpu_architecture, "CpuArchitecture") as any,
		related_publications: asyncify(data.related_publications, "RelatedItem") as any,
		related_datasets: asyncify(data.related_datasets, "RelatedItem") as any,
		development_status: asyncify(data.development_status, "RepoStatus") as any,
		operating_system: asyncify(data.operating_system, "OperatingSystem") as any,
		license: asyncify(data.license, "License") as any,
		related_region: asyncify(data.related_region, "Region") as any,
		keywords: asyncify(data.keywords, "Keyword") as any,
		related_software: asyncify(data.related_software, "RelatedItem") as any,
		interoperable_software: asyncify(data.interoperable_software, "RelatedItem") as any,
		funder: asyncify(data.funder, "Organization") as any,
		award: asyncify(data.award, "Award") as any,
		code_repository_url: data.code_repository_url,
		logo: data.logo,
		related_phenomena: asyncify(data.related_phenomena, "Phenomena") as any,
		submissionInfo: asyncify(data.submissionInfo, "SubmissionInfo") as any,
	};
}

export function createAsyncPersonData(data: PersonData): PersonDataAsync{
	return {
		id: data.id,
		given_name: data.given_name,
		family_name: data.family_name,
		identifier: data.identifier,
		affiliation: asyncify(data.affiliation, "Organization") as any,
	}
}