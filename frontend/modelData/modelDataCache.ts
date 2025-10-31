import type { PersonDataAsync, SoftwareDataAsync } from "./asyncModelData";
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

	private constructor(targetModel: ModelName) {
		this.targetModel = targetModel;
	}

	private static caches: Partial<{
		[M in ModelName]: ModelDataCache<AsyncModelTypeMap[M]>
	}> = {};

	public static getCache<M extends ModelName>(
		model: ModelName
	): ModelDataCache<AsyncModelTypeMap[M]> {

		if(!this.caches[model]){
			// TODO create cache
		}
		return this.caches[model] as ModelDataCache<AsyncModelTypeMap[M]>;
	}

	private targetModel: ModelName = null;
	private dataMap: Map<string, HSSIModelData> = new Map();

	public get model(): ModelName { return this.targetModel; }

	public static async getModelData(model: ModelName, uid: string): Promise<HSSIModelData> {
		const cache = this.getCache(model);
		const try2 = this.getCache("Software");
		return await cache.getData(uid);
	}

	public async getData(uid: string): Promise<T> {
		// TODO
		throw "not implemented";
	}
}