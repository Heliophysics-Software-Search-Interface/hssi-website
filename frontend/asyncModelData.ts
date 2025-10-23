import { 
	type ModelName, 
	type HSSIModelData,
	fetchTimeout
} from "./loader";

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
		// TODO
		fetchTimeout(apiModel + this.model + "/rows/" + this.id);
	}

	public async getData(): Promise<HSSIModelData>{
		if(this.data == null) await this.fetchData();
		return this.data;
	}
}