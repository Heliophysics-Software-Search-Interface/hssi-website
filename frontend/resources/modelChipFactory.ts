import { 
	fetchTimeout, 
	apiModel,
	apiSlugRowsAll,
	type JSONArray,
	type ControlledListData, 
	type GraphListData, 
	type HSSIModelData,
	type FunctionalityData,
	colorSrcGreen,
	type ModelDataAccess, 
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

export class BaseChipFactory implements ModelChipFactory, ModelDataAccess {

	private dataPromise: Promise<Response> = null;
	private jsonPromise: Promise<any> = null;
	protected modelName: string = "";
	protected modelData: JSONArray<HSSIModelData> = null;
	protected modelMap: Map<string, HSSIModelData> = null;

	public constructor(model: string){
		this.modelName = model;
		this.fetchModelData();
	}

	private async fetchModelData(): Promise<void> {
		if(this.modelData) return;
		if(this.jsonPromise || this.dataPromise) {
			await this.dataPromise;
			await this.jsonPromise;
			return;
		}
			
		try{
			const url = apiModel + this.modelName + apiSlugRowsAll;
			this.dataPromise = fetchTimeout(url);
			this.jsonPromise = (await this.dataPromise).json();
			this.modelData = (await this.jsonPromise).data;
			this.processData();
		}
		catch(e) {
			console.error(e);
		}

		this.dataPromise = null;
		this.jsonPromise = null;
	}

	private async buildMap(): Promise<void> {
		if(!this.modelData) await this.fetchModelData();
		this.modelMap = new Map();
		for(const data of this.modelData){
			this.modelMap.set(data.id, data);
		}
	}

	protected processData(): void { }

	protected async createChipFromData(_data: HSSIModelData): Promise<HTMLSpanElement> {
		const chip = document.createElement("span");
		chip.classList.add(styleItemChip);
		chip.innerText = "ITEM";
		return chip;
	}

	public async getModelData(): Promise<JSONArray<HSSIModelData>> {
		if(!this.modelData) await this.fetchModelData();
		return this.modelData;
	}

	public async getModelObject(uid: string): Promise<HSSIModelData> {
		if(!this.modelMap) await this.buildMap();
		return this.modelMap.get(uid);
	}

	public async createChip(uid: string): Promise<HTMLSpanElement> {
		const data = await this.getModelObject(uid);
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

export class ProgLangChipFactory extends UniformListChipFactory {

	public bgColor: string = "#FFF";
	public borderColor: string = colorSrcGreen;
	public textColor: string = colorSrcGreen;

	protected override processData(): void {
		for(const entry of this.modelData){
			
			const category = entry as FunctionalityData;
			switch(category.name.toLowerCase()) {
				case "javascript": category.abbreviation = "JaSc"; break;
				case "typescript": category.abbreviation = "TySc"; break;
				case "fortran77": category.abbreviation = "Fo77"; break;
				case "fortran90": category.abbreviation = "Fo90"; break;
				default:
					let splname = category.name.replaceAll(".", "").split(" ");
					switch(splname.length){
						case 2: 
						category.abbreviation = (
							splname[0].substring(0, 2) + 
							splname[1].substring(splname[1].length - 2, splname[1].length)
						);
						break;
						default:
							category.abbreviation = category.name.substring(0, 4);
							break;
					}
					break;
			}
		}
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