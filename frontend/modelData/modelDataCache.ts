import { 
	type PersonDataAsync, 
	type SoftwareDataAsync,
	type JSONArrayData,
	type JSONArray,
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
	"VerifiedSoftware" : SoftwareDataAsync,
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
			case "Software": return this.getCache("VerifiedSoftware") as any;
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
		model: M, uid: string | string[]
	): Promise<AsyncModelTypeMap[M] | AsyncModelTypeMap[M][]> {
		const cache = this.getCache(model);
		if(uid instanceof Array) return await cache.getMultiData(uid);
		else return await cache.getData(uid);
	}

	public static async fetchPage<M extends ModelName>(
		model: M,
		offset: number,
		limit: number
	): Promise<{ items: AsyncModelTypeMap[M][], total: number }> {
		const cache = this.getCache(model);
		return await cache.fetchPageData(offset, limit);
	}

	// Instance Implementation -------------------------------------------------

	private constructor(targetModel: ModelName) {
		this.targetModel = targetModel;
	}

	private static readonly BATCH_CHUNK_SIZE = 50;
	private static readonly BATCH_DELAY_MS = 100;

	private targetModel: ModelName = null;
	private dataMap: Map<string, T> = new Map();
	private promiseAll: Promise<void> = null;
	private allDataFetched: boolean = false;
	private batchQueue: string[] = [];
	private batchTimeout: ReturnType<typeof setTimeout> | null = null;
	private batchPromise: Promise<void> | null = null;
	private batchResolve: (() => void) | null = null;

	public get hasFetchedAllData(): boolean { return this.allDataFetched; }

	public get model(): ModelName { return this.targetModel; }

	private storeModelObjectData(obj: T): void {
		switch(this.model){
			case "VerifiedSoftware":
			case "Software": obj = createAsyncSoftwareData(obj as any) as any; break;
			case "Person": obj = createAsyncPersonData(obj as any) as any; break;
		}
		this.dataMap.set(obj.id, obj);
	}

	private async flushBatch(): Promise<void> {
		const uids = [...this.batchQueue];
		const resolve = this.batchResolve;
		this.batchQueue = [];
		this.batchTimeout = null;
		this.batchPromise = null;
		this.batchResolve = null;

		const missing = uids.filter(uid => !this.dataMap.has(uid));
		if (missing.length > 0) {
			const chunks: string[][] = [];
			for (let i = 0; i < missing.length; i += ModelDataCache.BATCH_CHUNK_SIZE) {
				chunks.push(missing.slice(i, i + ModelDataCache.BATCH_CHUNK_SIZE));
			}
			try {
				await Promise.all(chunks.map(chunk => this.fetchBatchChunk(chunk)));
			} catch(e) {
				console.error(`Error batch-fetching '${this.model}' data`, e);
			}
		}

		resolve();
	}

	private async fetchBatchChunk(uids: string[]): Promise<void> {
		const url = `${apiModel}${this.targetModel}${apiSlugRowsAll}?ids=${uids.join(",")}`;
		const result = await fetchTimeout(url);
		const data: JSONArrayData = await result.json();
		for (const obj of data.data) this.storeModelObjectData(obj as any);
	}

	private async fetchPageData(offset: number, limit: number): Promise<{ items: T[], total: number }> {
		if (this.allDataFetched) {
			const all = [...this.dataMap.values()];
			return { items: all.slice(offset, offset + limit), total: all.length };
		}
		const url = `${apiModel}${this.targetModel}${apiSlugRowsAll}?offset=${offset}&limit=${limit}`;
		const result = await fetchTimeout(url);
		const data = await result.json() as { data: JSONArray, total: number };
		const pageItems: T[] = [];
		for (const obj of data.data) {
			const raw = obj as any;
			this.storeModelObjectData(raw);
			pageItems.push(this.dataMap.get(raw.id));
		}
		return { items: pageItems, total: data.total };
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

	public async getMultiData(uids: string[]): Promise<T[]> {
		for(const uid of uids){
			if (!isUuid4(uid)) throw new Error(`${uid} is not a valid uuidv4`);
		}
		const promise = uids.map(uid => this.getData(uid));
		return await Promise.all(promise);
	}

	public async getData(uid: string): Promise<T> {

		if(!isUuid4(uid)) throw new Error(`${uid} is not properly formatted as uuid v4`);

		if (this.dataMap.has(uid)) return this.dataMap.get(uid);

		if (this.promiseAll) {
			await this.promiseAll;
			return this.dataMap.get(uid);
		}

		if (!this.batchQueue.includes(uid)) this.batchQueue.push(uid);

		if (!this.batchPromise) {
			this.batchPromise = new Promise<void>(resolve => { this.batchResolve = resolve; });
		}

		if (this.batchTimeout === null) {
			this.batchTimeout = setTimeout(
				() => this.flushBatch(), ModelDataCache.BATCH_DELAY_MS
			);
		}

		await this.batchPromise;
		return this.dataMap.get(uid);
	}

	/** 
	 * checks all the uids the cache currently has loaded and returns the 
	 * full uid for the first one that begins with the specified string,
	 * returns null if not found
	 */
	public expandUidFromTruncated(truncatedUid: string): string {
		for(const uid of this.dataMap.keys()){
			if(uid.startsWith(truncatedUid)) return uid;
		}
		return null;
	}
}

// make accessible to window
(window as any)[ModelDataCache.name] = ModelDataCache;