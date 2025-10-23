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
} from "../loader";

export const apiModel = "/api/models/";
export const apiSlugRowsAll = "/rows/all/";

export interface HssiDataAsync {
	id: string;
	data: HSSIModelData;
	get model(): ModelName;
	getData(): Promise<HssiDataAsync>;
}

export abstract class HssiModelDataAsync implements HSSIModelData, HssiDataAsync {
	
	private isFetchingData: boolean = false;

	public id: string = null;
	public data: HssiDataAsync = null;

	public abstract get model(): ModelName;
	
	public constructor(data: HSSIModelData){
		this.data = this.asyncifyData(data);
	}

	public static fromId(uid: string): HssiModelDataAsync{
		const instance: HssiModelDataAsync = new (this as any)();
		instance.id = uid;
		return instance;
	}

	protected abstract asyncifyData(data: HSSIModelData): HssiModelDataAsync;

	private async fetchData(): Promise<void>{
		if(this.isFetchingData || this.data) return;

		this.isFetchingData = true;
		try{
			const result = await fetchTimeout(apiModel + this.model + "/rows/" + this.id);
			const data: JSONObject = await result.json();
			this.data = this.asyncifyData(data as any);
			data.id = this.id
		} catch(e) {
			console.error(`Error fetching '${this.model}' data with id '${this.id}'`, e);
		}
		this.isFetchingData = false;
	}

	/**
	 * returns the hssi model object data if it is available, otherwise 
	 * asynchronously fetches it, then returns it when it is done
	 */
	public async getData(): Promise<HSSIModelData>{
		if(this.data == null) await this.fetchData();
		return this.data;
	}
}

class OrganizationDataAsync extends HssiModelDataAsync {

	name: string;
	/** ROR identifier url of the organization */
	identifier?: string;
	abbreviation: string;
	website: string;
	parent_organization: OrganizationDataAsync;

	public get model(): ModelName { return "Organization" }
	protected asyncifyData(data: HSSIModelData): HssiModelDataAsync {
		
	}
}

interface PersonDataAsync extends HSSIModelData {
	firstName: string,
	lastName: string,
	/** ORCID of the person */
	identifier?: string,
	affiliations: Array<HssiDataAsync<OrganizationDataAsync>>,
}

interface SoftwareDataAsync extends HSSIModelData {
	programmingLanguage: Array<HssiDataAsync<ControlledListData>>,
	publicationDate: string,
	publisher: HssiDataAsync<OrganizationDataAsync>,
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
	funder: HssiDataAsync<OrganizationDataAsync>,
	award: HssiDataAsync<HSSIModelData>,
	codeRepositoryUrl: string,
	logo: HssiDataAsync<HSSIModelData>,
	relatedPhenomena: Array<HssiDataAsync<ControlledListData>>,
	submissionInfo: HssiDataAsync<HSSIModelData>,
}