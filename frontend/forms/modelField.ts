import { Widget } from "../loader";

type WidgetType = new (elem: HTMLElement) => Widget;

type SerializedModel = {typeName: string, topField: string, subfields: Subfield[]};

export type Subfield = {
	name: string,
	model: string | ModelField,
	multi: boolean,
} & { [key: string]: any };

/**
 * Represents a widget with attributes and a subfield layout that in theory 
 * should be able to handle infinite levels of depth
 */
export class ModelField {
	
	/** arbitrary attributes */
	[key: string]: any;

	public widgetType: string | WidgetType = "";

	/** The name to use to refer to this model */
	public typeName: string = "";
	public topField: string | Subfield = "";
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
	
	private static modelMap: Map<string, ModelField> = new Map();

	public static BasicWidget(
		type: WidgetType, multi: boolean = false, attrs: {[key: string]: any}
	) {
		const model = new ModelField();
		model.widgetType = type;
		model.topField = {
			name: "self",
			model: model,
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
	public static parseModels(serializedModels: SerializedModel[]): ModelField[] {
		const models: ModelField[] = [];

		// map model type names to model
		for(const obj of serializedModels) {
			const model = new ModelField();
			for(const field in model){
				model[field] = model[field];
			}
			this.modelMap.set(model.typeName, model);
		}

		// convert subfield types from strings to references
		for(const model of models){
			let topFieldFound = typeof model.topField === "string";
			for(const subfield of model.subfields) {

				// swap out top field if subfield with matching name found
				if(!topFieldFound && model.topField === subfield.name){
					model.topField = subfield;
					topFieldFound = true;
				}

				if(typeof subfield.type === "string") {
					let type = this.modelMap.get(subfield.type);
					if (type != null) subfield.type = type;
					else console.error(
						`Invalid type '${subfield.type}' on subfield ` + 
						`'${subfield.name}' in model '${model.typeName}'`
					);
				}
			}

			if(!topFieldFound) console.error(
				`No top field '${model.topField}' found for model '${model.typeName}'`
			);
		}

		return models;
	}
}