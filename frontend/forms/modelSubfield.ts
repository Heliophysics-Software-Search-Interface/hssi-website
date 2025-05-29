import {
	deepMerge,
	formRowStyle, ModelFieldStructure, RequirementLevel, Widget,
    type PropertyContainer, type SerializedSubfield,
} from "../loader";

const labelStyle = "custom-label";
const multiFieldRowStyle = "multi-field-row";
const multiFieldPartStyle = "multi-field-part";
const tooltipWrapperStyle = "tooltip-wrapper";
const tooltipIconStyle = "tooltip-icon";
const tooltipTextStyle = "tooltip-text";
const explanationTextStyle = "explanation-text";
const indentStyle = "indent";

/**
 * represents a single field in the db model and information related to 
 * rendering/interacting with it in the form
 */
export class ModelSubfield {

	public name: string = "";
	public type: ModelFieldStructure = null;
	public requirement: RequirementLevel = RequirementLevel.OPTIONAL;
	public properties: PropertyContainer = {};
	public widget: Widget = null;
	public containerElement: HTMLDivElement = null;

	private labelElement: HTMLLabelElement = null;
	private explanationElement: HTMLDivElement = null;

	private subfieldContainer: HTMLDetailsElement = null;
	private subfields: ModelSubfield[] = [];

	public get multi(): boolean { return false; }

	protected constructor(
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

	protected buildFieldInfo(): void {

		// create the label text
		this.labelElement = document.createElement("label");
		this.labelElement.innerHTML = this.properties.label ?? this.name;
		this.labelElement.classList.add(labelStyle);
		this.containerElement.appendChild(this.labelElement);

		// create the "hover for info" icon
		if(this.properties.tooltipBestPractise != null){
			const ttbpWrapper = document.createElement("span") as HTMLSpanElement;
			ttbpWrapper.classList.add(tooltipWrapperStyle);
			
			const ttbpIcon = document.createElement("span") as HTMLSpanElement;
			ttbpIcon.classList.add(tooltipIconStyle);
			ttbpIcon.innerText = "i";

			const ttbpText = document.createElement("div") as HTMLDivElement;
			ttbpText.classList.add(tooltipTextStyle);
			ttbpText.innerText = this.properties.tooltipBestPractise;
			
			ttbpWrapper.appendChild(ttbpIcon);
			ttbpWrapper.appendChild(ttbpText);
			this.labelElement.appendChild(ttbpWrapper);
		}

		// create the help text below the label if it exists
		if(this.properties.tooltipExplanation != null){
			this.explanationElement = document.createElement("div");
			this.explanationElement.classList.add(explanationTextStyle);
			this.explanationElement.innerHTML = this.properties.tooltipExplanation;
			this.containerElement.appendChild(this.explanationElement);
		}
	}

	protected buildWidget(): void {
		if(!this.type){
			console.error("Undefined subfield type!", this);
			return;
		}
		const widgetType = this.type.getWidgetType();
		if(widgetType == null) {
			console.error(`Unrecognized widget type on '${this.name}'`, this.type);
			return;
		}
		this.widget = new widgetType(document.createElement("div"), this);
		if(this.properties.widgetProperties != null) {
			this.widget.properties = deepMerge(
				this.widget.properties, 
				this.properties.widgetProperties
			);
		}
		this.widget.properties.requirementLevel = this.requirement;
		this.widget.initialize();
		this.containerElement.appendChild(this.widget.element);
	}

	private buildSubfieldContainer(): void {

		// don't need a subfield container if no subfields
		if(this.type.subfields.length <= 0) return;

		// create expandable details container
		this.subfieldContainer = document.createElement("details");
		const summary = document.createElement("summary");
		this.subfieldContainer.appendChild(summary);
		this.subfieldContainer.classList.add(indentStyle);
		this.containerElement.appendChild(this.subfieldContainer);

		// create subfields when container expanded
		this.subfieldContainer.addEventListener("click", e => this.onExpandSubfields(e));

		// this.hideSubfieldContianer();
	}

	private buildSubFields(): void{

		// parse and build each serialized subfield
		for(const serializedField of this.type.subfields){
			const field = ModelSubfield.parse(serializedField)
			const row = document.createElement("div") as HTMLDivElement;
			row.classList.add(formRowStyle)
			field.buildInterface(row);
			this.subfields.push(field);
			this.subfieldContainer.appendChild(row);
		}
	}

	private onExpandSubfields(_: Event = null): void{
		if(!this.subfieldsAreBuilt()) this.buildSubFields();
	}

	/** 
	 * expand the subfield container and show the content and build 
	 * subfields if necessary 
	 */
	public expandSubfields(): void {
		if(this.subfieldsExpanded() || this.subfieldsHidden()) return;
		this.onExpandSubfields();
		this.subfieldContainer.setAttribute("open", "");
	}

	/** shows the subfield container and expand button */
	public showSubfieldContainer(): void {
		if(this.subfields.length <= 0 || this.subfieldContainer == null) return;
		this.subfieldContainer.style.display = "block";
	}

	/** hide and clear the subfield container and expand button */
	public hideSubfieldContianer(): void {
		if(this.subfieldContainer == null) return;
		this.subfieldContainer.removeAttribute("open");
		this.subfieldContainer.style.display = "none";
		this.clearSubfields();
	}

	/** destroy the field and remove it from the form */
	public destroy(): void {
		this.clearSubfields();
		if(this.widget != null){
			if(this.widget.element != null){
				this.widget.element.remove();
			}
		}
		if(this.containerElement != null){
			this.containerElement.remove();
		}
		this.widget = null;
		this.containerElement = null;
		this.labelElement = null;
		this.explanationElement = null;
		this.subfieldContainer = null;
	}

	/** destroy and clear all subfields from the form */
	public clearSubfields(): void {
		for(const field of this.subfields){
			field.destroy();
		}
		this.subfields.length = 0;
	}

	/** true if the field should use data from it's subfields */
	public hasSubfields(): boolean {
		return this.subfields.length > 0;
	}

	/** return true if the subfields are expanded and not hidden */
	public subfieldsExpanded(): boolean {
		if(this.subfieldContainer == null) return false; 
		if(this.subfieldContainer.style.display == "none") return false; 
		return this.subfieldContainer.hasAttribute("open");
	}

	public subfieldsHidden(): boolean {
		return( 
			this.subfieldContainer == null || 
			this.subfieldContainer.style.display == "none"
		);
	}

	/** 
	 * returns true if the subfields have been built. Basically if the 
	 * subfield container has ever been expanded or not
	 */
	public subfieldsAreBuilt(): boolean {
		return this.subfields.length === this.type.subfields.length;
	}

	/** get the data that the field has received from user input */
	public getFieldData(): {[key: string]: any} | string | any[] {
		if(!this.hasSubfields()) {
			return this.widget?.getInputValue() ?? "";
		}
		const data: {[key: string]: any} = {};
		for(const subfield of this.subfields){
			data[subfield.name] = subfield.getFieldData();
		}
		return data
	}

	/** 
	 * builds the html ui elements required to render and interact with this 
	 * field for the db model
	 * @param targetDiv the target container to build the ui inside of
	 */
	public buildInterface(
		targetDiv: HTMLDivElement, 
		buildFieldInfo: boolean = true,
	): void {
		this.containerElement = document.createElement("div");

		if(buildFieldInfo) this.buildFieldInfo();
		this.buildWidget();
		this.buildSubfieldContainer();

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

	private multiFieldContainerElement: HTMLDivElement = null;
	private multiFields: ModelSubfield[] = [];

	private newItemButton: HTMLButtonElement = null;

	protected getRowContainer(): HTMLDivElement {
		if(this.multiFieldContainerElement == null) this.buildMultiFieldContainer();
		return this.multiFieldContainerElement;
	}
	
	private createMultifield(): ModelSubfield {
		return new ModelSubfield(
			this.name, 
			this.type, 
			this.requirement, 
			this.properties
		);
	}

	private buildNewMultifield(): void {

		// create row for button to right of field
		const multiRow = document.createElement("div") as HTMLDivElement;
		multiRow.classList.add(multiFieldRowStyle);

		// create field
		const fieldContainer = document.createElement("div") as HTMLDivElement;
		fieldContainer.classList.add(multiFieldPartStyle);
		const field = this.createMultifield();
		field.buildInterface(fieldContainer, false);

		// create button for removing the field entry
		const removeButton = document.createElement("button") as HTMLButtonElement;
		removeButton.type = "button";
		removeButton.innerText = "- remove";

		// remove on click
		removeButton.addEventListener("click", () => {
			const fieldIndex = this.multiFields.indexOf(field);
			this.multiFields.splice(fieldIndex, 1);
			field.destroy();
			multiRow.remove();
		});

		// add elements to root node
		this.multiFields.push(field);
		multiRow.appendChild(fieldContainer);
		multiRow.appendChild(removeButton);
		this.getRowContainer().appendChild(multiRow);
	}

	public buildInterface(
		targetDiv: HTMLDivElement, 
		buildFieldInfo: boolean = true
	): void {
		this.containerElement = document.createElement("div");

		if(buildFieldInfo) this.buildFieldInfo();
		this.buildMultiFieldContainer();
		this.buildNewMultifield();
		this.buildNewItemButton();

		targetDiv.appendChild(this.containerElement);
	}

	public destroy(): void {
		super.destroy();
		this.multiFields.length = 0;
		this.multiFieldContainerElement = null;
		this.newItemButton = null;
	}

	private buildMultiFieldContainer(): void {

		// this has the potential to be built multiple times so its important 
		// to check it hasn't already been built
		if(this.multiFieldContainerElement != null) return;

		this.multiFieldContainerElement = document.createElement("div");
		this.containerElement.appendChild(this.multiFieldContainerElement);
	}

	private buildNewItemButton(): void{
		this.newItemButton = document.createElement("button");
		this.newItemButton.type = "button";
		this.newItemButton.innerText = "+ add";
		this.newItemButton.addEventListener(
			"click", () => this.onNewItemPressed()
		);
		this.containerElement.appendChild(this.newItemButton);
	}

	private onNewItemPressed(): void {
		this.buildNewMultifield();
	}

	public getFieldData(): { [key: string]: any; } | string | any[] {
		const arr: any[] = [];
		for(const field of this.multiFields) {
			const fieldVal = field.getFieldData();
			if(fieldVal != null && fieldVal !== "") arr.push(fieldVal);
		}
		return arr;
	}
}