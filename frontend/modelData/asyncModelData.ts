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
	data: HSSIModelData;
	getData(): Promise<HSSIModelData>;
}

export class AsyncHssiData implements AsyncHssiModelData {
	
	private isFetchingData: boolean = false;

	public id: string = null;
	public model: ModelName = null;
	public data: HSSIModelData = null;
	
	public constructor(model: ModelName, id: string){
		this.model = model;
		this.id = id;
	}

	private async fetchData(): Promise<void>{
		try{
			const result = await fetchTimeout(apiModel + this.model + "/rows/" + this.id);
			const data: JSONObject = await result.json();
			this.data = data as any;
			data.id = this.id
		} catch(e) {
			console.error(`Error fetching '${this.model}' data with id '${this.id}'`, e);
		}
	}

	public async getData(): Promise<HSSIModelData>{
		if(this.data == null) await this.fetchData();
		return this.data;
	}
}