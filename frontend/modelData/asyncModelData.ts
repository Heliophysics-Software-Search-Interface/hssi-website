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
	getData(): Promise<T>;
}

export class HssiModelDataAsync<T extends HSSIModelData> 
	implements HSSIModelData, HssiDataAsync<T> 
{
	private objId: string = null;
	private modelData: T = null;
	private dataFetchPromise: Promise<void> = null;

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
	firstName: string,
	lastName: string,
	/** ORCID of the person */
	identifier?: string,
	affiliations: Array<HssiDataAsync<OrganizationData>>,
}

export interface SoftwareDataAsync extends HSSIModelData {
	programmingLanguage: Array<HssiDataAsync<ControlledListData>>,
	publicationDate: string,
	publisher: HssiDataAsync<OrganizationData>,
	authors: Array<HssiDataAsync<PersonDataAsync>>,
	relatedInstruments: Array<HssiDataAsync<ControlledListData>>,
	relatedObservatories: Array<HssiDataAsync<ControlledListData>>,
	softwareName: string,
	version: HssiDataAsync<VersionData>,
	persistentIdentifier: string,
	referencePublication: HssiDataAsync<ControlledListData>,
	description: string,
	conciseDescription: string,
	documentation: string,
	softwareFunctionality: Array<HssiDataAsync<FunctionalityData>>,
	dataSources: Array<HssiDataAsync<ControlledListData>>,
	inputFormats: Array<HssiDataAsync<ControlledListData>>,
	outputFormats: Array<HssiDataAsync<ControlledListData>>,
	cpuArchitecture: Array<HssiDataAsync<ControlledListData>>,
	relatedPublications: Array<HssiDataAsync<ControlledListData>>,
	relatedDatasets: Array<HssiDataAsync<ControlledListData>>,
	developmentStatus: HssiDataAsync<ControlledListData>,
	operatingSystem: Array<HssiDataAsync<ControlledListData>>,
	license: Array<HssiDataAsync<ControlledListData>>,
	relatedRegion: Array<HssiDataAsync<ControlledListData>>,
	keywords: Array<KeywordData>,
	relatedSoftware: Array<HssiDataAsync<ControlledListData>>,
	interoperableSoftware: Array<HssiDataAsync<ControlledListData>>,
	funder: Array<HssiDataAsync<OrganizationData>>,
	award: HssiDataAsync<HSSIModelData>,
	codeRepositoryUrl: string,
	logo: HssiDataAsync<HSSIModelData>,
	relatedPhenomena: Array<HssiDataAsync<ControlledListData>>,
	submissionInfo: HssiDataAsync<HSSIModelData>,
}

// -----------------------------------------------------------------------------

function asyncifyUid<T extends HSSIModelData>(
	obj: JSONObject | string,
	targetModel: ModelName,
): HssiDataAsync<T> {
	let id = obj;
	if((obj as any).id) id = (obj as any).id;
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
	if(obj instanceof Array) return asyncifyJsonArray<T>(obj, targetModel);
	else return asyncifyUid<T>(obj, targetModel);
}

export function createAsyncSoftwareData(data: SoftwareData): SoftwareDataAsync{
	return {
		id: data.id,
		programmingLanguage: asyncify(data.programmingLanguage, "ProgrammingLanguage") as any,
		publicationDate: data.publicationDate,
		publisher: asyncify(data.publisher, "Organization") as any,
		authors: asyncify(data.authors, "Person") as any,
		relatedInstruments: asyncify(data.relatedInstruments, "InstrumentObservatory") as any,
		relatedObservatories: asyncify(data.relatedObservatories, "InstrumentObservatory") as any,
		softwareName: data.softwareName,
		version: asyncify(data.version, "SoftwareVersion") as any,
		persistentIdentifier: data.persistentIdentifier,
		referencePublication: asyncify(data.referencePublication, "RelatedItem") as any,
		description: data.description,
		conciseDescription: data.conciseDescription,
		documentation: data.documentation,
		softwareFunctionality: asyncify(data.softwareFunctionality, "FunctionCategory") as any,
		dataSources: asyncify(data.dataSources, "DataInput") as any,
		inputFormats: asyncify(data.inputFormats, "FileFormat") as any,
		outputFormats: asyncify(data.outputFormats, "FileFormat") as any,
		cpuArchitecture: asyncify(data.cpuArchitecture, "CpuArchitecture") as any,
		relatedPublications: asyncify(data.relatedPublications, "RelatedItem") as any,
		relatedDatasets: asyncify(data.relatedDatasets, "RelatedItem") as any,
		developmentStatus: asyncify(data.developmentStatus, "RepoStatus") as any,
		operatingSystem: asyncify(data.operatingSystem, "OperatingSystem") as any,
		license: asyncify(data.license, "License") as any,
		relatedRegion: asyncify(data.relatedRegion, "Region") as any,
		keywords: asyncify(data.keywords, "Keyword") as any,
		relatedSoftware: asyncify(data.relatedSoftware, "RelatedItem") as any,
		interoperableSoftware: asyncify(data.interoperableSoftware, "RelatedItem") as any,
		funder: asyncify(data.funder, "Organization") as any,
		award: asyncify(data.award, "Award") as any,
		codeRepositoryUrl: data.codeRepositoryUrl,
		logo: asyncify(data.logo, "Image") as any,
		relatedPhenomena: asyncify(data.relatedPhenomena, "Phenomena") as any,
		submissionInfo: asyncify(data.submissionInfo, "SubmissionInfo") as any,
	};
}

export function createAsyncPersonData(data: PersonData): PersonDataAsync{
	return {
		id: data.id,
		firstName: data.firstName,
		lastName: data.lastName,
		identifier: data.identifier,
		affiliations: asyncify(data.affiliations, "Organization") as any,
	}
}