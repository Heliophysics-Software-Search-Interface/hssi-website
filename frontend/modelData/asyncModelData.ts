import { 
	type ModelName, 
	type HSSIModelData,
	type JSONObject,
	fetchTimeout,
} from "../loader";

export const apiModel = "/api/models/";
export const apiSlugRowsAll = "/rows/all/";

export interface AsyncHssiModelData {
	id: string;
	model: ModelName;
	data: AsyncHssiModelData;
	getData(): Promise<AsyncHssiModelData>;
}

export class AsyncHssiData implements AsyncHssiModelData {
	
	private isFetchingData: boolean = false;

	public id: string = null;
	public model: ModelName = null;
	public data: AsyncHssiModelData = null;
	
	public constructor(model: ModelName, id: string){
		this.model = model;
		this.id = id;
	}

	private async fetchData(): Promise<void>{
		if(this.isFetchingData || this.data) return;

		this.isFetchingData = true;
		try{
			const result = await fetchTimeout(apiModel + this.model + "/rows/" + this.id);
			const data: JSONObject = await result.json();
			this.data = data as any;
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
	public async getData(): Promise<AsyncHssiModelData>{
		if(this.data == null) await this.fetchData();
		return this.data;
	}
}