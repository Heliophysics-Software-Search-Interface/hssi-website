import { 
	colorSrcGreen,
	type ControlledListData, 
	type GraphListData, 
	type HSSIModelData,
	type FunctionalityData,
	type ModelName,
	ModelDataCache,
} from "../loader";

const styleItemChip = "item-chip";
const styleItemNametag = "item-nametag";
const styleSubchip = "subchip";

export interface ModelChipFactory {
	/** 
	 * create a small display element that can be used to represent a database 
	 * listing anywhere in the document
	 */
	createChip(uid: string): Promise<HTMLSpanElement>;

	createNametag(uid: string): Promise<HTMLSpanElement>;
}

export class BaseChipFactory<T extends HSSIModelData> implements ModelChipFactory {

	protected modelName: ModelName = null;

	public constructor(model: ModelName){
		this.modelName = model;
	}

	protected processData(): void { }

	protected getAbbreviationFromData(data: T): string { return data.id.substring(0, 4); }

	protected getNameFromData(data: T): string { return data.id; }

	protected createChipFromData(data: T): HTMLSpanElement {
		const chip = document.createElement("span");
		chip.classList.add(styleItemChip);
		chip.innerText = this.getAbbreviationFromData(data);
		return chip;
	}

	protected createNametagFromData(data: T): HTMLSpanElement {
		const tag = this.createChipFromData(data);
		tag.classList.add(styleItemNametag);
		tag.innerText = this.getNameFromData(data);
		return tag;
	}

	public async createChip(uid: string): Promise<HTMLSpanElement> {
		const data = await ModelDataCache.getModelData(this.modelName, uid);
		return this.createChipFromData(data as any);
	}

	public async createNametag(uid: string): Promise<HTMLSpanElement> {
		const data = await ModelDataCache.getModelData(this.modelName, uid);
		return this.createNametagFromData(data as any);
	}
}

export class ControlledListChipFactory<T extends ControlledListData> extends BaseChipFactory<T> {
	protected override getAbbreviationFromData(data: T): string {
		return data.name.substring(0, 4);
	}
	protected override getNameFromData(data: T): string {
		return data.name;
	}
	protected override createChipFromData(data: T): HTMLSpanElement {
		const listData = data as T;
		const chip = super.createChipFromData(listData);
		chip.innerText = this.getAbbreviationFromData(listData);
		chip.title = listData.name;
		return chip;
	}
}

export class UniformListChipFactory extends ControlledListChipFactory<ControlledListData> {

	public bgColor: string = "#FFF";
	public borderColor: string = "#000";
	public textColor: string = "#000";
	
	protected override getAbbreviationFromData(data: ControlledListData): string {
		return data.abbreviation || super.getAbbreviationFromData(data);
	}

	protected override createChipFromData(data: HSSIModelData): HTMLSpanElement {
		const listData = data as ControlledListData;
		const chip = super.createChipFromData(listData);
		chip.style.backgroundColor = this.bgColor;
		chip.style.borderColor = this.borderColor;
		chip.style.borderStyle = "solid";
		chip.style.borderWidth = "1px";
		chip.style.color = this.textColor;
		chip.innerText = listData.abbreviation as string || chip.innerText;
		return chip
	}
}

export class GraphListChipFactory<T extends GraphListData> extends ControlledListChipFactory<T> {

	protected override getAbbreviationFromData(data: T): string {
		return data.abbreviation || super.getAbbreviationFromData(data);
	}

	protected override createChipFromData(data: GraphListData): HTMLSpanElement {
		const graphData = data as T;
		const chip = super.createChipFromData(graphData);
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

	protected override getAbbreviationFromData(data: ControlledListData): string {
		let label = "";
		switch(data.name.toLowerCase()) {
			case "javascript": label = "JaSc"; break;
			case "typescript": label = "TySc"; break;
			case "fortran77": label = "Fo77"; break;
			case "fortran90": label = "Fo90"; break;
			default:
				let splname = data.name.replaceAll(".", "").split(" ");
				switch(splname.length){
					case 2:
					label = (
						splname[0].substring(0, 2) + 
						splname[1].substring(splname[1].length - 2, splname[1].length)
					);
					break;
					default:
						label = data.name.substring(0, 4);
						break;
				}
				break;
		}
		return label;
	}
}

export class FunctionCategoryChipFactory extends GraphListChipFactory<FunctionalityData> {

	protected override createChipFromData(data: FunctionalityData): HTMLSpanElement {
		const funcData = data as FunctionalityData;
		const chip = super.createChipFromData(data);
		chip.style.backgroundColor = funcData.backgroundColor;
		chip.style.borderColor = funcData.backgroundColor;
		chip.style.color = funcData.textColor;
		chip.innerText = this.getAbbreviationFromData(data);
		return chip;
	}
}