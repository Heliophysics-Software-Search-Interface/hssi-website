import { 
	RequirementLevel, Widget, ModelSubfield
} from "../loader";

type WidgetType = new (elem: HTMLElement) => Widget;

export type PropertyContainer = {

	/** the title that will be shown above the field, if not specified field name will be used */
	label?: string,

	/** the small font explanation that will be shown below the label */
	tooltipExplanation?: string,

	/** the tooltip that appears on hover of the information icon */
	tooltipBestPractise?: string,

} & { [key: string]: any };

type SerializedFieldStructure = {
	typeName: string, 
	subfields: SerializedSubfield[]
};

type ModelFieldStructureInstance = {
	topField: ModelSubfield,
	subFields: ModelSubfield[],
}

export type SerializedSubfield = {
	name: string,
	type: string | ModelFieldStructure,
	multi: boolean,
	requirement: RequirementLevel,
	properties: PropertyContainer,
};

/**
 * Represents a field type with attributes and a subfield layout that in theory 
 * should be able to handle infinite levels of depth
 */
export class ModelFieldStructure {
	
	/** arbitrary attributes */
	[key: string]: any;

	public widgetType: string | WidgetType = "";

	/** The type name to use to refer to this field structure layout */
	public typeName: string = "";
	public topField: SerializedSubfield = null;
	public subfields: SerializedSubfield[] = [];

	private constructor() { }

	/** get the top-level widget to display for this model */
	public getWidgetType(): WidgetType {

		// if the structure does not have a direct widget type, we can find it 
		// through the top field
		if(this.widgetType == null || this.widgetType === "") {
			let widgetType = this.widgetType;
			let structure: ModelFieldStructure = this;
			while (widgetType == null || widgetType === "") {
				if(structure?.topField == null) {
					console.error("Widget type cannot be resolved for " + this.typeName);
					return null;
				}
				let structureNext = this.topField.type;
				if(!(structureNext instanceof ModelFieldStructure)){
					structureNext = ModelFieldStructure.getFieldStructure(structureNext);
				}
				structure = structureNext;
				widgetType = structureNext?.widgetType;
			}
			this.widgetType = widgetType;
		}

		// find widget type if not yet parsed
		if ((this.widgetType as any).prototype === undefined){
			const widgetTypeName = this.widgetType as string;
			this.widgetType = Widget.getRegisteredWidget(widgetTypeName);
		}

		return this.widgetType as WidgetType;
	}

	/** create fields for the whole structure */
	public generateInstance(): ModelFieldStructureInstance {
		const subfields: ModelSubfield[] = [];

		const topField = this.topField ? ModelSubfield.parse(this.topField) : null;
		for(const sub of this.subfields) {
			subfields.push(ModelSubfield.parse(sub));
		}

		return {
			topField: topField,
			subFields: subfields,
		};
	}
	
	private static fieldStructureMap: Map<string, ModelFieldStructure> = new Map();

	public static getFieldStructure(fieldType: string): ModelFieldStructure {
		return this.fieldStructureMap.get(fieldType);
	}

	// public static basicWidget(
	// 	type: WidgetType, 
	// 	requirement = RequirementLevel.OPTIONAL, 
	// 	multi: boolean = false, 
	// 	attrs: PropertyContainer,
	// ): ModelFieldStructure {
	// 	const model = new ModelFieldStructure();
	// 	model.widgetType = type;
	// 	model.topField = {
	// 		name: "SELF",
	// 		type: model,
	// 		multi: multi,
	// 		requirement: requirement,
	// 		properties: attrs,
	// 	}
	// 	model.subfields.push(model.topField);
	// 	return model;
	// }

	/**
	 * create basic widget models from registered widgets and parse them as
	 * model field structures
	 */
	public static parseBasicWidgetModels(): void {
		for(const widgetType of Widget.getAllRegisteredWidgets()){
			const structure = new ModelFieldStructure();
			structure.typeName = widgetType.name;
			structure.widgetType = widgetType;
			this.fieldStructureMap.set(widgetType.name, structure)
		}
	}

	/**
	 * parse and register the given serialized models
	 * @param serializedModels 
	 */
	public static parseModels(serializedModels: SerializedFieldStructure[]): ModelFieldStructure[] {
		const models: ModelFieldStructure[] = [];

		// map model type names to model
		for(const obj of serializedModels) {
			const model = new ModelFieldStructure();
			for(const field in obj){
				model[field] = (obj as any)[field];
			}

			// top field will always be first field in subfields
			model.topField = obj.subfields.shift();
			this.fieldStructureMap.set(model.typeName, model);
			models.push(model);
		}

		// convert subfield types from strings to references
		for(const model of models){
			for(const subfield of model.subfields) {
				if(typeof subfield.type === "string") {
					let type = this.fieldStructureMap.get(subfield.type);
					if (type != null) subfield.type = type;
					else console.error(
						`Invalid type '${subfield.type}' on subfield ` + 
						`'${subfield.name}' in model '${model.typeName}'`
					);
				}
			}
		}

		return models;
	}
}
