import { 
	BaseChipFactory,
	colorSrcGreen,
	ControlledListChipFactory,
	FunctionCategoryChipFactory,
	ProgLangChipFactory,
	type ModelChipFactory,
	type ModelName,
} from "../loader";

export class ModelChipBuilder {
	private static factoryMap: Map<string, ModelChipFactory> = new Map();
	
	private static buildFactory(model: ModelName): ModelChipFactory{
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
}