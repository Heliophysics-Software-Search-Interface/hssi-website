import { 
	fetchTimeout, 
	apiModel,
	apiSlugRowsAll,
	type JSONArray,
	type ControlledListData, 
	type GraphListData, 
	type HSSIModelData,
	type FunctionalityData, 
} from "../loader";

const styleItemChip = "item-chip";
const styleSubchip = "subchip";

export interface ModelChipFactory {
	/** 
	 * create a small display element that can be used to represent a database 
	 * listing anywhere in the document
	 */
	createChip(uid: string): Promise<HTMLSpanElement>;
}

export class BaseChipFactory implements ModelChipFactory {

	protected modelName: string = "";
	protected modelData: JSONArray<HSSIModelData> = null;
	protected modelMap: Map<string, HSSIModelData> = null;

	public constructor(model: string){
		this.modelName = model;
		this.fetchModelData();
	}

	private async fetchModelData(): Promise<void> {
		const url = apiModel + this.modelName + apiSlugRowsAll;
		const result = await fetchTimeout(url);
		this.modelData = (await result.json()).data;
	}

	private async buildMap(): Promise<void> {
		if(!this.modelData) await this.fetchModelData();
		this.modelMap = new Map();
		for(const data of this.modelData){
			this.modelMap.set(data.id, data);
		}
	}

	protected async createChipFromData(_data: HSSIModelData): Promise<HTMLSpanElement> {
		const chip = document.createElement("span");
		chip.classList.add(styleItemChip);
		chip.innerText = "ITEM";
		return chip;
	}

	protected async getModelData(uid: string): Promise<HSSIModelData> {
		if(!this.modelMap) await this.buildMap();
		return this.modelMap.get(uid);
	}

	public async createChip(uid: string): Promise<HTMLSpanElement> {
		const data = await this.getModelData(uid);
		return await this.createChipFromData(data);
	}
}

export class ControlledListChipFactory extends BaseChipFactory {
	protected override async createChipFromData(data: HSSIModelData): Promise<HTMLSpanElement> {
		const listData = data as ControlledListData;
		const chip = await super.createChipFromData(listData);
		chip.innerText = listData.name.substring(0,4);
		return chip;
	}
}

export class UniformListChipFactory extends ControlledListChipFactory {

	public bgColor: string = "#FFF";
	public borderColor: string = "#000";
	public textColor: string = "#000";

	protected override async createChipFromData(data: HSSIModelData): Promise<HTMLSpanElement> {
		const listData = data as ControlledListData;
		const chip = await super.createChipFromData(listData);
		chip.style.backgroundColor = this.bgColor;
		chip.style.borderColor = this.borderColor;
		chip.style.borderStyle = "solid";
		chip.style.borderWidth = "1px";
		chip.style.color = this.textColor;
		chip.innerText = listData.abbreviation as string || chip.innerText;
		return chip
	}
}

export class GraphListChipFactory extends ControlledListChipFactory {
	protected override async createChipFromData(data: HSSIModelData): Promise<HTMLSpanElement> {
		const graphData = data as GraphListData;
		const chip = await super.createChipFromData(graphData);
		if(graphData.parents?.length > 0) {
			chip.classList.add(styleSubchip);
		}
		return chip;
	}
}

export class FunctionCategoryChipFactory extends GraphListChipFactory {
	protected override async createChipFromData(data: HSSIModelData): Promise<HTMLSpanElement> {
		const funcData = data as FunctionalityData;
		const chip = await super.createChipFromData(data);
		chip.style.backgroundColor = funcData.backgroundColor;
		chip.style.borderColor = funcData.backgroundColor;
		chip.style.color = funcData.textColor;
		chip.innerText = funcData.abbreviation;
		return chip;
	}
}