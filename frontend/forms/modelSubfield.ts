import {
    ModelFieldStructure, RequirementLevel, Widget,
    type PropertyContainer, type SerializedSubfield,
} from "../loader";

const labelStyle = "custom-label";
const tooltipWrapperStyle = "tooltip-wrapper";
const tooltipIconStyle = "tooltip-icon";
const tooltipTextStyle = "tooltip-text";
const explanationTextStyle = "explanation-text";

/**
 * represents a single field in the db model and information related to 
 * rendering/interacting with it in the form
 */
export class ModelSubfield {

	public name: string = "";

	public type: ModelFieldStructure = null;

	public requirement: RequirementLevel = RequirementLevel.OPTIONAL;
	
	public properties: PropertyContainer = {};

	private containerElement: HTMLDivElement = null;

	private labelElement: HTMLLabelElement = null;

	private explanationElement: HTMLDivElement = null;

	private widget: Widget = null;

	public get multi(): boolean { return false; }

	public constructor(
		name: string, 
		type: ModelFieldStructure, 
		requirement: RequirementLevel = RequirementLevel.OPTIONAL,
		properties: PropertyContainer = {},
	) {
		this.name = name;
		this.type = type;
		this.requirement = requirement;
		this.properties = properties;
	}

	private buildFieldInfo(targetDiv: HTMLDivElement): void {

		// create the label text
		this.labelElement = document.createElement("label");
		this.labelElement.innerHTML = this.properties.label ?? this.name;
		this.labelElement.classList.add(labelStyle);
		targetDiv.appendChild(this.labelElement);

		// create the "hover for info" icon
		if(this.properties.tooltipBestPractice != null){
			const ttbpWrapper = document.createElement("span") as HTMLSpanElement;
			ttbpWrapper.classList.add(tooltipWrapperStyle);
			
			const ttbpIcon = document.createElement("span") as HTMLSpanElement;
			ttbpIcon.classList.add(tooltipIconStyle);
			ttbpIcon.innerText = "i";

			const ttbpText = document.createElement("div") as HTMLDivElement;
			ttbpIcon.classList.add(tooltipTextStyle);
			ttbpText.innerText = this.properties.tooltipBestPractice;
			
			ttbpWrapper.appendChild(ttbpIcon);
			ttbpWrapper.appendChild(ttbpText);
			this.labelElement.appendChild(ttbpWrapper);
			targetDiv.appendChild(ttbpWrapper);
		}

		// create the help text below the label if it exists
		if(this.properties.tooltipExplanation != null){
			this.explanationElement = document.createElement("div");
			this.explanationElement.classList.add(explanationTextStyle);
			this.explanationElement.innerHTML = this.properties.tooltipExplanation;
		}
	}

	private buildWidget(targetDiv: HTMLDivElement): void {
		if(!this.type){
			console.error("Undefined subfield type!");
			return;
		}
		const widgetType = this.type.getWidgetType();
		if(widgetType == null) {
			console.error(`Undefined type on '${this.name}'`);
			return;
		}
		this.widget = new widgetType(document.createElement("div"));
		this.widget.initialize();
		targetDiv.appendChild(this.widget.element);
		console.log(this.widget);
	}

	/** 
	 * builds the html ui elements required to render and interact with this 
	 * field for the db model
	 * @param targetDiv the target container to build the ui inside of
	 */
	public buildInterface(targetDiv: HTMLDivElement): void {
		this.containerElement = document.createElement("div");
		
		this.buildFieldInfo(this.containerElement);
		this.buildWidget(this.containerElement);

		// TODO build subfields

		targetDiv.appendChild(this.containerElement);
	}

	/** whether or not the field has already built its UI elements */
	public isBuilt(): boolean {
		return this.widget != null;
	}

	/** parse serialized subfield data into a functional subfield field object */
	public static parse(data: SerializedSubfield): ModelSubfield {

		// get field structure type if not yet parsed
		let type = data.type; 
		if(!(type instanceof ModelFieldStructure)) {
			type = ModelFieldStructure.getFieldStructure(type);
			data.type = type;
		}

		// create and return the subfield object
		let subfield: ModelSubfield = null;
		if(!data.multi){
			subfield = new ModelSubfield(
				data.name, 
				type, 
				data.requirement,
				data.properties,
			);
		}
		else {
			subfield = new ModelMultiSubfield(
				data.name, 
				type, 
				data.requirement, 
				data.properties
			)
		}
		return subfield;
	}
}

export class ModelMultiSubfield extends ModelSubfield {
	public get multi(): boolean { return true; }
}