import {
	deepMerge, formRowStyle, ModelFieldStructure, RequirementLevel, 
	Widget, ModelMultiSubfield, FieldRequirement,
	type PropertyContainer, type SerializedSubfield, type JSONValue,
	type JSONObject,
	type AnyInputElement,
	ModelBox,
	SimpleEvent,
} from "../../loader";

export const labelStyle = "custom-label";
const tooltipWrapperStyle = "tooltip-wrapper";
const tooltipIconStyle = "tooltip-icon";
const tooltipTextStyle = "tooltip-text";
export const explanationTextStyle = "explanation-text";
const subfieldContainerStyle = "subfield-container";
export const requiredIndicatorStyle = "required-indicator";
const indentStyle = "indent";

const faInfoCircle = "<i class='fa fa-info-circle'></i>";

/**
 * represents a single field in the db model and information related to 
 * rendering/interacting with it in the form
 */
export class ModelSubfield {

	public name: string = "";
	public rowName: string = "";
	public type: ModelFieldStructure = null;
	public properties: PropertyContainer = {};
	public widget: Widget = null;
	public containerElement: HTMLDivElement = null;
	public requirement: FieldRequirement = null;

	protected controlContainerElement: HTMLDivElement = null;
	protected labelElement: HTMLLabelElement = null;
	private explanationElement: HTMLDivElement = null;

	protected readOnly: boolean = false;
	protected condensed: boolean = false;
	
	private subfieldContainer: HTMLDetailsElement = null;
	private subfields: ModelSubfield[] = [];
	private parentField: ModelSubfield = null;

	public get parent(): ModelSubfield { return this.parentField; }
	public get multi(): boolean { return false; }

	public onValueChanged: SimpleEvent = new SimpleEvent();
	public onChildValueChanged: SimpleEvent = new SimpleEvent();

	/// Initialization ---------------------------------------------------------

	protected constructor(
		name: string,
		rowName: string,
		type: ModelFieldStructure, 
		properties: PropertyContainer = {},
	) {
		this.name = name;
		this.rowName = rowName;
		this.type = type;
		this.properties = properties;

		this.onValueChanged.addListener(() => {
			if(this.parent) this.parent.onChildValueChanged.triggerEvent();
		});
		this.onChildValueChanged.addListener(() =>{
			if(this.parent) this.parent.onChildValueChanged.triggerEvent();
		});
	}

	private buildSubfieldContainer(): void {

		// don't need a subfield container if no subfields
		if(this.type.subfields.length <= 0) return;

		// create expandable details container
		this.subfieldContainer = document.createElement("details");
		this.subfieldContainer.classList.add(subfieldContainerStyle);
		const summary = document.createElement("summary");
		this.subfieldContainer.appendChild(summary);
		this.subfieldContainer.classList.add(indentStyle);
		this.controlContainerElement.appendChild(this.subfieldContainer);

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
			field.buildInterface(row, true, this.readOnly, this.condensed);
			field.parentField = this;
			this.subfields.push(field);
			this.subfieldContainer.appendChild(row);
		}
	}

	private onExpandSubfields(_: Event = null): void{
		if(!this.subfieldsAreBuilt()) this.buildSubFields();
	}

	protected buildFieldInfo(): void {

		// create the label text
		this.labelElement = document.createElement("label");
		this.labelElement.innerHTML = this.properties.label ?? this.name;
		this.labelElement.classList.add(labelStyle);
		this.containerElement.appendChild(this.labelElement);

		if(this.properties.requirementLevel >= 2) {
			this.labelElement.innerHTML = (
				this.labelElement.innerHTML + 
				` <span class=${requiredIndicatorStyle}>*</span>`
			);
		}

		// create the "hover for info" icon
		if(this.properties.tooltipExplanation != null){
			const ttbpWrapper = document.createElement("span") as HTMLSpanElement;
			ttbpWrapper.classList.add(tooltipWrapperStyle);
			
			const ttbpIcon = document.createElement("span") as HTMLSpanElement;
			ttbpIcon.classList.add(tooltipIconStyle);
			ttbpIcon.innerHTML = faInfoCircle;

			const ttbpText = document.createElement("div") as HTMLDivElement;
			ttbpText.classList.add(tooltipTextStyle);
			ttbpText.innerText = this.properties.tooltipExplanation;
			
			ttbpWrapper.appendChild(ttbpIcon);
			ttbpWrapper.appendChild(ttbpText);
			this.labelElement.appendChild(ttbpWrapper);
		}

		// create the help text below the label if it exists
		if(this.properties.tooltipBestPractise != null){
			this.explanationElement = document.createElement("div");
			this.explanationElement.classList.add(explanationTextStyle);
			this.explanationElement.innerHTML = this.properties.tooltipBestPractise;
			this.containerElement.appendChild(this.explanationElement);
		}
	}

	protected buildWidget(readOnly: boolean): void {
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
		this.widget.initialize(readOnly);
		this.controlContainerElement.appendChild(this.widget.element);
	}

	/** 
	 * builds the html ui elements required to render and interact with this 
	 * field for the db model
	 * @param targetDiv the target container to build the ui inside of
	 */
	public buildInterface(
		targetDiv: HTMLDivElement, 
		buildFieldInfo: boolean = true,
		readOnly: boolean = false,
		condensed: boolean = false,
	): void {
		this.readOnly = readOnly;
		this.condensed = condensed;
		if(this.containerElement != null) {
			console.warn(`Interface for ${this.name} is already built`);
			return;
		}
		this.containerElement = document.createElement("div");

		if(buildFieldInfo) this.buildFieldInfo();

		this.controlContainerElement = document.createElement("div");
		this.buildWidget(readOnly);
		this.buildSubfieldContainer();
		this.containerElement.appendChild(this.controlContainerElement);

		targetDiv.appendChild(this.containerElement);
		this.requirement = new FieldRequirement(
			this, this.properties.requirementLevel ?? RequirementLevel.OPTIONAL
		);
		this.requirement.containerElement = this.controlContainerElement;
	}

	/// Public functionality ---------------------------------------------------

	public applyValidityStyles(): void {
		if(this.requirement == null) return;
		this.requirement.applyRequirementWarningStyles();
		for(const subfield of this.subfields){
			subfield.applyValidityStyles();
		}
	}

	public clearField(): void {
		
		// clear input value
		this.setValue("", true);

		// clear/collapse all subfield values
		for(const subfield of this.getSubfields()) {
			subfield.clearField();
			subfield.collapseSubfields();
			subfield.requirement.removeStyles();
		}

		this.collapseSubfields();
		this.requirement.removeStyles();
	}

	public fillField(data: JSONValue, notify: boolean = true): void {
		
		if(data instanceof Array) {
			if(this instanceof ModelMultiSubfield) this.fillMultiFields(data);
			else {
				console.warn(`Data for ${this.name} is an array but field is not multi`);
			}
			return;
		}

		if(this.widget == null) {
			console.warn(`Widget for ${this.name} is not built yet`);
			return;
		}

		// controlled list item
		if(data instanceof Object && data.name && data.id){
			if(this.widget instanceof ModelBox){
				const find = () => {
					const modelbox = this.widget as ModelBox
					const op = modelbox.options.find(val => { return val.id == data.id; });
					modelbox.selectOption(op);
				};
				if(this.widget.options) find();
				else setTimeout(find, 0);
			}
		}

		// if its a nested field data
		else if(data instanceof Object) {
			this.expandSubfields();
			const fields = this.getSubfields();
			for(const key in data){
				const value = data[key];

				// check each field/subfield of this field and apply the data
				if(this.name === key || this.rowName === key) {
					this.fillField(value, notify);
					continue;
				}
				for(const subfield of fields){
					if(subfield.name === key || subfield.rowName === key){
						subfield.fillField(value, notify);
						break;
					}
				}
			}
		}

		// it's a non-recursive value (almost certainly a string)
		else this.setValue(data.toString(), notify);
	}

	public meetsRequirementLevel(): boolean {
		if(
			this.requirement == null || 
			this.requirement.level == RequirementLevel.OPTIONAL
		) {
			return true;
		}
		return this.hasValidInput();
	}

	public hasValidInput(): boolean {
		if(this.widget instanceof ModelBox){
			if(!this.widget.properties.allowNewEntries){
				if(!this.getInputElement().data){
					return false;
				}
			}
		}
		
		const value = this.widget?.getInputValue();
		if(!value) return false;

		const inputElem = this.getInputElement();
		if(inputElem) return inputElem.checkValidity();

		return true;
	}

	public hasValidFormatValue(): boolean {
		const inputElem = this.getInputElement();
		if(inputElem) return inputElem.checkValidity();
		return true;
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

	public collapseSubfields(): void {
		if(!this.subfieldsExpanded() || this.subfieldsHidden()) return;
		this.subfieldContainer.removeAttribute("open");
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
		this.widget?.destroy();
		if(this.containerElement != null){
			this.containerElement.remove();
		}
		if(this.requirement != null && !this.requirement.field.multi){
			this.requirement.destroy();
			this.requirement = null;
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

	public getSubfields(): ModelSubfield[] {
		return this.subfields;
	}

	public getInputElement(): AnyInputElement {
		return this.widget?.getInputElement() ?? null;
	}

	public setValue(value: string, notify: boolean = true): void {
		this.widget?.setValue(value, notify);
	}

	/** 
	 * returns true if the subfields have been built. Basically if the 
	 * subfield container has ever been expanded or not
	 */
	public subfieldsAreBuilt(): boolean {
		return this.subfields.length === this.type.subfields.length;
	}

	/** get the data that the field has received from user input */
	public getFieldData(): JSONValue {
		if(!this.hasSubfields()) {
			return this.widget?.getInputValue() ?? "";
		}
		const data: JSONObject = {};
		data[this.name] = this.widget?.getInputValue() ?? "";
		for(const subfield of this.subfields){
			data[subfield.name] = subfield.getFieldData();
		}
		return data;
	}

	/** whether or not the field has already built its UI elements */
	public isBuilt(): boolean {
		return this.widget != null;
	}
		
	/** returns the subfields and the subfields within those subfields, etc */
	public static getSubfieldsRecursive(
		subfield: ModelSubfield, 
		onlyRelevant: boolean = true,
		returnVal: ModelSubfield[] = []
	): ModelSubfield[] {

		for(const field of subfield.subfields){
			returnVal.push(field);
			if(
				(
					field.requirement.level >= RequirementLevel.MANDATORY && 
					field.hasValidInput()
				) || !onlyRelevant
			){
				this.getSubfieldsRecursive(field, onlyRelevant, returnVal);
			}
		}

		return returnVal;
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
				data.rowName,
				type, 
				data.properties,
			);
		}
		else {
			subfield = new ModelMultiSubfield(
				data.name,
				data.rowName,
				type,
				data.properties
			)
		}
		subfield.properties.requirementLevel = data.requirement;

		return subfield;
	}
}
