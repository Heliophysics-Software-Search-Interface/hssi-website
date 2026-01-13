import { 
	BaseChipFactory,
	ControlledListChipFactory,
	FunctionCategoryChipFactory,
	UniformListChipFactory,
	type HSSIModelData,
	type JSONArray,
	type ModelChipFactory,
	type ModelName,
} from "../loader";

export const colorSrcGreen = "#559e41";

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
				let langFactory = new UniformListChipFactory(model);
				langFactory.bgColor = "#FFF";
				langFactory.borderColor = colorSrcGreen;
				langFactory.textColor = colorSrcGreen;
				langFactory.nameMap = {
					"Javascript": "JaSc",
					"Typescript": "TySc",
					"Fortran77": "Fo77",
					"Fortran90": "Fo90",
				};
				factory = langFactory;
				break;
			case "Region":
				let regionFactory = new UniformListChipFactory(model);
				regionFactory.bgColor = "#CDF";
				regionFactory.borderColor = "#24A";
				regionFactory.textColor = regionFactory.borderColor;
				regionFactory.nameMap = {
					"Earth Atmosphere": "EAtm",
					"Earth Magnetosphere": "EMag",
					"Interplanetary Space": "Spce",
					"Planetary Magnetospheres": "PMag",
					"Solar Environment": "Solr",
				}
				factory = regionFactory;
				break;
			case "Phenomena":
				let phenomFactory = new UniformListChipFactory(model);
				phenomFactory.bgColor = "#ECF";
				phenomFactory.borderColor = "#608";
				phenomFactory.textColor = phenomFactory.borderColor;
				factory = phenomFactory;
				break;
			case "DataInput":
				let sourceFactory = new UniformListChipFactory(model);
				sourceFactory.bgColor = "#222";
				sourceFactory.borderColor = "#2FB";
				sourceFactory.textColor = sourceFactory.borderColor;
				factory = sourceFactory;
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