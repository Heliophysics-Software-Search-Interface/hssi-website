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
const styleSubchip = "subchip";

export interface ModelChipFactory {
	/** 
	 * create a small display element that can be used to represent a database 
	 * listing anywhere in the document
	 */
	createChip(uid: string): Promise<HTMLSpanElement>;
}

export class BaseChipFactory<T extends HSSIModelData> implements ModelChipFactory {

	protected modelName: ModelName = null;

	public constructor(model: ModelName){
		this.modelName = model;
	}

	protected processData(): void { }

	protected createChipFromData(_data: T): HTMLSpanElement {
		const chip = document.createElement("span");
		chip.classList.add(styleItemChip);
		chip.innerText = "ITEM";
		return chip;
	}

	public async createChip(uid: string): Promise<HTMLSpanElement> {
		const data = await ModelDataCache.getModelData(this.modelName, uid);
		return this.createChipFromData(data as any);
	}
}

export class ControlledListChipFactory<T extends ControlledListData> extends BaseChipFactory<T> {
	protected override createChipFromData(data: T): HTMLSpanElement {
		const listData = data as T;
		const chip = super.createChipFromData(listData);
		chip.innerText = listData.name.substring(0,4);
		chip.title = listData.name;
		return chip;
	}
}

export class UniformListChipFactory extends ControlledListChipFactory<ControlledListData> {

	public bgColor: string = "#FFF";
	public borderColor: string = "#000";
	public textColor: string = "#000";

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

	protected override createChipFromData(data: ControlledListData): HTMLSpanElement {
		const chip = super.createChipFromData(data);

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

		chip.innerText = label;
		return chip;
	}
}

export class FunctionCategoryChipFactory extends GraphListChipFactory<FunctionalityData> {

	protected override createChipFromData(data: FunctionalityData): HTMLSpanElement {
		const funcData = data as FunctionalityData;
		const chip = super.createChipFromData(data);
		chip.style.backgroundColor = funcData.backgroundColor;
		chip.style.borderColor = funcData.backgroundColor;
		chip.style.color = funcData.textColor;
		chip.innerText = funcData.abbreviation;
		return chip;
	}
}