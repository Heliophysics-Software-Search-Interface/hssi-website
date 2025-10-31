import { fetchTimeout, type JSONObject } from "../util";
import { apiModel, createAsyncPersonData, createAsyncSoftwareData, type PersonDataAsync, type SoftwareDataAsync } from "./asyncModelData";
import { 
	type ControlledListData,
	type FunctionalityData,
	type GraphListData,
	type HSSIModelData,
	type KeywordData,
	type ModelName, 
	type OrganizationData,
	type VersionData
} from "./modelStructure";

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

	public get model(): ModelName { return this.targetModel; }

	private async fetchData(uid: string): Promise<void> {

		// prevent simultaneous fetch calls
		const existingPromise = this.promiseMap.get(uid);
		if(existingPromise){
			await existingPromise;
			return;
		}

		// fetch data through api and format to async if possible
		try{
			const result = await fetchTimeout(apiModel + this.targetModel + "/rows/" + uid);
			const data: JSONObject = result.json();
			
			let modelObj: T = data as any;
			switch(this.model){
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

	public async getData(uid: string): Promise<T> {

		let promise = this.promiseMap.get(uid);
		if(promise) await promise;
		else {
			let promise = this.fetchData(uid);
			this.promiseMap.set(uid, promise);
			await promise;
		}
		
		return this.dataMap.get(uid);
	}
}