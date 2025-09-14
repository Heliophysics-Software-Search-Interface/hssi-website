import { 
	BaseChipFactory,
	ControlledListChipFactory,
	FunctionCategoryChipFactory,
	ProgLangChipFactory,
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
	private static factoryMap: Map<string, ModelChipFactory & ModelDataAccess> = new Map();
	
	private static buildFactory(model: ModelName): ModelChipFactory & ModelDataAccess{
		let factory: BaseChipFactory = null;

		switch(model){
			case "FunctionCategory":
				factory = new FunctionCategoryChipFactory(model);
				break;
			case "ProgrammingLanguage":
				factory = new ProgLangChipFactory(model);
				break;
			default: factory = new ControlledListChipFactory(model); break;
		}

		this.factoryMap.set(model, factory);
		return factory;
	}

	public static async createChip(model: ModelName, uid: string): Promise<HTMLSpanElement> {
		let factory = this.factoryMap.get(model);
		if(!factory) factory = this.buildFactory(model);
		return await factory.createChip(uid);
	}

	public static async getModelData(model: ModelName): Promise<JSONArray<HSSIModelData>> {
		let factory = this.factoryMap.get(model);
		if(!factory) factory = this.buildFactory(model);
		return await factory.getModelData();
	}

	public static async getModelObject(model: ModelName, uid: string){
		let factory = this.factoryMap.get(model);
		if(!factory) factory = this.buildFactory(model);
		return await factory.getModelObject(uid);
	}
}