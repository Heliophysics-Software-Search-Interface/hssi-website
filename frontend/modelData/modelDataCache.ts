import { 
	type PersonDataAsync, 
	type SoftwareDataAsync,
	type JSONArrayData, 
	type JSONArray, 
	type JSONObject,
	type ControlledListData,
	type FunctionalityData,
	type GraphListData,
	type HSSIModelData,
	type KeywordData,
	type ModelName, 
	type OrganizationData,
	type VersionData,
	apiModel, 
	apiSlugRowsAll, 
	createAsyncPersonData, 
	createAsyncSoftwareData, 
	fetchTimeout,
	isUuid4,
} from "../loader";

interface AsyncModelTypeMap {
	"HSSIModel" : HSSIModelData,
	"HssiSet" : HSSIModelData,
	"ControlledList" : ControlledListData,
	"ControlledGraphList" : GraphListData,
	"Keyword" : KeywordData,
	"OperatingSystem" : ControlledListData,
	"CpuArchitecture" : ControlledListData,
	"Phenomena" : ControlledListData,
	"RepoStatus" : ControlledListData,
	"Image" : HSSIModelData,
	"ProgrammingLanguage" : ControlledListData,
	"DataInput" : ControlledListData,
	"FileFormat" : ControlledListData,
	"Region" : ControlledListData,
	"InstrumentObservatory" : ControlledListData,
	"FunctionCategory" : FunctionalityData,
	"License" : ControlledListData,
	"Organization" : OrganizationData,
	"Software" : SoftwareDataAsync,
	"SoftwareVersion" : VersionData,
	"VisibleSoftware" : SoftwareDataAsync,
	"SoftwareEditQueue" : HSSIModelData,
	"SubmissionInfo" : HSSIModelData,
	"Award" : ControlledListData,
	"RelatedItem" : ControlledListData,
	"Person" : PersonDataAsync,
	"Submitter" : HSSIModelData,
	"Curator" : HSSIModelData,
}

export class ModelDataCache<T extends HSSIModelData>{

	private static caches: Partial<{
		[M in ModelName]: ModelDataCache<AsyncModelTypeMap[M]>
	}> = {};

	public static getCache<M extends ModelName>(
		model: M
	): ModelDataCache<AsyncModelTypeMap[M]> {

		// link models together who represent the same thing
		switch(model){
			case "Software": return this.getCache("VisibleSoftware") as any;
		}

		if(!this.caches[model]){
			const cache = new ModelDataCache(model);
			this.caches[model] = cache as any;
		}
		return this.caches[model] as ModelDataCache<AsyncModelTypeMap[M]>;
	}

	public static async getModelDataAll<M extends ModelName>(
		model: M
	): Promise<Iterable<AsyncModelTypeMap[M]>> {
		const cache = this.getCache(model);
		if(!cache.allDataFetched) await cache.fetchAllData();
		return cache.dataMap.values();
	}

	public static async getModelData<M extends ModelName>(
		model: M, uid: string
	): Promise<AsyncModelTypeMap[M]> {
		const cache = this.getCache(model);
		return await cache.getData(uid);
	}

	// Instance Implementation -------------------------------------------------

	private constructor(targetModel: ModelName) {
		this.targetModel = targetModel;
	}

	private targetModel: ModelName = null;
	private dataMap: Map<string, T> = new Map();
	private promiseMap: Map<string, Promise<void>> = new Map();
	private promiseAll: Promise<void> = null;
	private allDataFetched: boolean = false;

	public get model(): ModelName { return this.targetModel; }

	private storeModelObjectData(obj: T): void {
		switch(this.model){
			case "VisibleSoftware":
			case "Software": obj = createAsyncSoftwareData(obj as any) as any; break;
			case "Person": obj = createAsyncPersonData(obj as any) as any; break;
		}
		this.dataMap.set(obj.id, obj);
	}

	private async fetchData(uid: string): Promise<void> {

		// prevent simultaneous fetch calls
		if(this.promiseAll){
			await this.promiseAll;
			return;
		}
		const existingPromise = this.promiseMap.get(uid);
		if(existingPromise){
			await existingPromise;
			return;
		}

		// fetch data through api and format to async if possible
		try{
			console.log(`Fetching data ${uid} from ${this.model}`);
			const result = await fetchTimeout(apiModel + this.targetModel + "/rows/" + uid);
			const data: JSONObject = await result.json();
			this.storeModelObjectData(data as any);
		}
		catch(e){
			console.error(`Error fetching '${this.model}' data with id '${uid}'`, e);
		}

		// remove promise to signal it is no longer fetching the data with specified uid
		this.promiseMap.delete(uid);
	}

	private async fetchAllModelData(): Promise<void> {

		// prevent multiple and/or simultaneous fetch alls
		if(this.promiseAll) await this.promiseAll;
		if(this.allDataFetched) return;

		// fetch the data and parse it int
		const result = await fetchTimeout(apiModel + this.targetModel + apiSlugRowsAll);
		const data: JSONArrayData = await result.json();
		for(const obj of data.data) this.storeModelObjectData(obj as any);

		// reset the promise
		this.allDataFetched = true;
		this.promiseAll = null;
	}

	/**
	 * Preemptively fetches data for all model objects that are available for 
	 * the model that this model cache targets
	 */
	public async fetchAllData(): Promise<void> {

		if(this.promiseAll) {
			await this.promiseAll;
			return;
		}
		
		// fetch all data and set promise flag
		console.log(`Fetching all data from ${this.model}`);
		this.promiseAll = this.fetchAllModelData();
		await this.promiseAll;
	}

	public async getData(uid: string): Promise<T> {

		if(!isUuid4(uid)) {
			throw new Error(`${uid} is not properly formatted as uuid v4`);
		}

		// fetch data if not already downloaded
		if(!this.dataMap.has(uid)){
			let promise = this.promiseMap.get(uid);
			if(promise) await promise;
			else {
				let promise = this.fetchData(uid);
				this.promiseMap.set(uid, promise);
				await promise;
			}
		}
		
		return this.dataMap.get(uid);
	}
}

// make accessible to window
(window as any)[ModelDataCache.name] = ModelDataCache;