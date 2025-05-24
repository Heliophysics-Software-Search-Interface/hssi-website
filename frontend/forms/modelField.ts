import { Widget } from "../loader";

type WidgetType = new (elem: HTMLElement) => Widget;

type KvContainer = { [key: string]: any };

type SerializedFieldStructure = {
	typeName: string, 
	subfields: Subfield[]
};

export type Subfield = {
	name: string,
	type: string | ModelFieldStructure,
	multi: boolean,
} & KvContainer;

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
	public topField: Subfield = null;
	public subfields: Subfield[] = [];

	private constructor() { }

	/** get the top-level widget to display for this model */
	public getWidgetType(): WidgetType {

		// find widget type if not yet parsed
		if ((this.widgetType as any).prototype === undefined){
			const widgetTypeName = this.widgetType as string;
			this.widgetType = Widget.getRegisteredWidget(widgetTypeName);
		}

		return this.widgetType as WidgetType;
	}
	
	private static modelMap: Map<string, ModelFieldStructure> = new Map();

	public static BasicWidget(
		type: WidgetType, multi: boolean = false, attrs: {[key: string]: any}
	) {
		const model = new ModelFieldStructure();
		model.widgetType = type;
		model.topField = {
			name: "SELF",
			type: model,
			multi: multi,
			...attrs,
		}
		model.subfields.push(model.topField);
		return model;
	}

	public static isSubfieldValidated(subfield: Subfield): boolean {
		return subfield.topField !== undefined;
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
			this.modelMap.set(model.typeName, model);
		}

		// convert subfield types from strings to references
		for(const model of models){
			for(const subfield of model.subfields) {
				if(typeof subfield.type === "string") {
					let type = this.modelMap.get(subfield.type);
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