import { RequirementLevel, Widget } from "../loader";

type WidgetType = new (elem: HTMLElement) => Widget;

type PropertyContainer = {

	/** the title that will be shown above the field, if not specified field name will be used */
	label?: string,

	/** the small font explanation that will be shown below the label */
	tooltipExplanation?: string,

	/** the tooltip that appears on hover of the information icon */
	tooltipBestPractice?: string,
	
} & { [key: string]: any };

type SerializedFieldStructure = {
	typeName: string, 
	subfields: SerializedSubfield[]
};

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

		// find widget type if not yet parsed
		if ((this.widgetType as any).prototype === undefined){
			const widgetTypeName = this.widgetType as string;
			this.widgetType = Widget.getRegisteredWidget(widgetTypeName);
		}

		return this.widgetType as WidgetType;
	}
	
	private static fieldStructureMap: Map<string, ModelFieldStructure> = new Map();

	public static getFieldStructure(fieldType: string): ModelFieldStructure {
		return this.fieldStructureMap.get(fieldType);
	}

	public static basicWidget(
		type: WidgetType, 
		requirement = RequirementLevel.OPTIONAL, 
		multi: boolean = false, 
		attrs: PropertyContainer,
	) {
		const model = new ModelFieldStructure();
		model.widgetType = type;
		model.topField = {
			name: "SELF",
			type: model,
			multi: multi,
			requirement: requirement,
			properties: attrs,
		}
		model.subfields.push(model.topField);
		return model;
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

/**
 * represents a single field in the db model and information related to 
 * rendering/interacting with it in the form
 */
export class ModelSubfield {

	public name: string = "";

	public type: ModelFieldStructure = null;

	public multi: boolean = false;

	public requirement: RequirementLevel = RequirementLevel.OPTIONAL;

	public properties: PropertyContainer = {};

	public constructor(
		name: string, 
		type: ModelFieldStructure, 
		multi: boolean = false,
		requirement: RequirementLevel = RequirementLevel.OPTIONAL,
		properties: PropertyContainer = {},
	) {
		this.name = name;
		this.type = type;
		this.multi = multi;
		this.requirement = requirement;
		this.properties = properties;
	}

	/** 
	 * builds the html ui elements required to render and interact with this 
	 * field for the db model
	 * @param targetDiv the target container to build the ui inside of
	 */
	public buildWidgets(targetDiv: HTMLDivElement): void {
		
	}

	/** parse serialized subfield data into a functional subfield field object */
	public static parse(data: SerializedSubfield): ModelSubfield {

		// get field structure type if not yet parsed
		let type = data.type; 
		if(!(type instanceof ModelFieldStructure)) {
			type =  ModelFieldStructure.getFieldStructure(type);
			data.type = type;
		}

		// create and return the subfield object
		const field = new ModelSubfield(
			data.name, 
			type, 
			data.multi,
			data.requirement,
			data.properties,
		);
		return field;
	}
}