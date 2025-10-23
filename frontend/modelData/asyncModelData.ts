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
} from "../loader";

export const apiModel = "/api/models/";
export const apiSlugRowsAll = "/rows/all/";

export interface HssiDataAsync<T extends HSSIModelData> {
	id: string;
	data: HSSIModelData;
	get model(): ModelName;
	getData(): Promise<T>;
}

export abstract class HssiModelDataAsync<T extends HSSIModelData> 
	implements HSSIModelData, HssiDataAsync<T> 
{
	private dataFetchPromise: Promise<void> = null;

	public id: string = null;
	public data: T = null;

	public abstract get model(): ModelName;
	
	public constructor(data: HSSIModelData){
		this.data = this.asyncifyData(data);
	}

	public static fromId<T2 extends HSSIModelData>(uid: string): HssiModelDataAsync<T2>{
		const instance: HssiModelDataAsync<T2> = new (this as any)();
		instance.id = uid;
		return instance;
	}

	protected abstract asyncifyData(data: HSSIModelData): T;

	private async fetchData(): Promise<void>{
		if(this.data) return;
		if(this.dataFetchPromise){
			await this.dataFetchPromise;
			return;
		}

		try{
			const result = await fetchTimeout(apiModel + this.model + "/rows/" + this.id);
			const data: JSONObject = await result.json();
			this.data = this.asyncifyData(data as any);
			data.id = this.id
		} catch(e) {
			console.error(`Error fetching '${this.model}' data with id '${this.id}'`, e);
		}

		this.dataFetchPromise = null;
	}

	/**
	 * returns the hssi model object data if it is available, otherwise 
	 * asynchronously fetches it, then returns it when it is done
	 */
	public async getData(): Promise<T>{
		if(this.data == null) {
			if(this.dataFetchPromise) {
				await this.dataFetchPromise;
			}
			else{
				this.dataFetchPromise = this.fetchData();
				await this.dataFetchPromise;
			}
		}
		return this.data;
	}
}

interface PersonDataAsync extends HSSIModelData {
	firstName: string,
	lastName: string,
	/** ORCID of the person */
	identifier?: string,
	affiliations: Array<HssiDataAsync<OrganizationData>>,
}

interface SoftwareDataAsync extends HSSIModelData {
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
	funder: HssiDataAsync<OrganizationData>,
	award: HssiDataAsync<HSSIModelData>,
	codeRepositoryUrl: string,
	logo: HssiDataAsync<HSSIModelData>,
	relatedPhenomena: Array<HssiDataAsync<ControlledListData>>,
	submissionInfo: HssiDataAsync<HSSIModelData>,
}