import { 
	BaseChipFactory,
	ControlledListChipFactory,
	FunctionCategoryChipFactory,
	ProgLangChipFactory,
	UniformListChipFactory,
	type HSSIModelData,
	type JSONArray,
	type ModelChipFactory,
	type ModelName,
} from "../loader";

export interface ModelDataAccess {
	/** get all the data in a specified model table as a json array of each row */
	getModelData(): Promise<JSONArray<HSSIModelData>>;
	/** get a specific row with the specified uid in the model table */
	getModelObject(uid: string): Promise<HSSIModelData>;
}

export class ModelData {
	private static factoryMap: Map<string, ModelChipFactory> = new Map();
	
	private static buildFactory(model: ModelName): ModelChipFactory {
		let factory: BaseChipFactory<HSSIModelData> = null;

		switch(model){
			case "VisibleSoftware":
			case "Software":
				factory = new BaseChipFactory(model); break;
			case "FunctionCategory":
				factory = new FunctionCategoryChipFactory(model);
				break;
			case "ProgrammingLanguage":
				factory = new ProgLangChipFactory(model);
				break;
			case "Region":
				let ufact = new UniformListChipFactory(model);
				ufact.bgColor = "#CDF";
				ufact.borderColor = "#24A";
				ufact.textColor = ufact.borderColor;
				ufact.nameMap = {
					"Earth Atmosphere": "EAtm",
					"Earth Magnetosphere": "EMag",
					"Interplanetary Space": "Spce",
					"Planetary Magnetospheres": "PMag",
					"Solar Environment": "Solr",
				}
				factory = ufact;
				break;
			default: 
				factory = new ControlledListChipFactory(model); 
				break;
		}

		this.factoryMap.set(model, factory);
		return factory;
	}

	public static async createChip(model: ModelName, uid: string): Promise<HTMLSpanElement> {
		let factory = this.factoryMap.get(model);
		if(!factory) factory = this.buildFactory(model);
		return await factory.createChip(uid);
	}

	public static async createNametag(model: ModelName, uid: string): Promise<HTMLSpanElement> {
		let factory = this.factoryMap.get(model);
		if(!factory) factory = this.buildFactory(model);
		return await factory.createNametag(uid);
	}
}