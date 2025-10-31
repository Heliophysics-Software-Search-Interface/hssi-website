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

	public get model(): ModelName { return this.targetModel; }

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
			
			let modelObj: T = data as any;
			switch(this.model){
				case "VisibleSoftware":
				case "Software": modelObj = createAsyncSoftwareData(data as any) as any; break;
				case "Person": modelObj = createAsyncPersonData(data as any) as any; break;
			}

			this.dataMap.set(uid, modelObj);
		}
		catch(e){
			console.error(`Error fetching '${this.model}' data with id '${uid}'`, e);
		}

		// remove promise to signal it is no longer fetching the data with specified uid
		this.promiseMap.delete(uid);
	}

	public async fetchAllData(): Promise<void> {

		if(this.promiseAll) return;
		// TODO set this.promiseAll
		console.log(`Fetching all data from ${this.model}`);

		// fetch data for all rows
		const result = await fetchTimeout(apiModel + this.targetModel + apiSlugRowsAll);
		const json: JSONArrayData = await result.json()
		const array: JSONArray<HSSIModelData> = json.data;
		
		// convert objects to async where possible
		let datas: Array<T> = [];
		switch(this.model){
			case "VisibleSoftware":
			case "Software":
				for(const data of array){
					datas.push(createAsyncSoftwareData(data as any) as any);
				}
				break;
			case "Person": 
				for(const data of array){
					datas.push(createAsyncPersonData(data as any) as any);
				}
				break;
			default: datas = array as any; break;
		}

		// register all objects in map
		for(const obj of datas) this.dataMap.set(obj.id, obj);

		this.promiseAll = null;
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