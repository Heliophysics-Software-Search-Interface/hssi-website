import {
	FieldRequirement, ModelSubfield,
	RequirementLevel,
	type AnyInputElement,
	type JSONArray,
	type JSONValue,
} from "../../loader";

export const faCloseIcon = "<i class='fa fa-close'></i>";
const multiFieldRowStyle = "multi-field-row";
const multiFieldPartStyle = "multi-field-part";
const multiFieldContainerStyle = "multifield-container";

type MultiField = ModelSubfield & {destroyRow?: () => void };

/**
 * A special type of {@link ModelSubfield} which can be used to dynamically 
 * allow users to add multiple entries of the same type to a field
 */
export class ModelMultiSubfield extends ModelSubfield {

	private multiFieldContainerElement: HTMLDivElement = null;
	private newItemButton: HTMLButtonElement = null;
	private hideButton: HTMLButtonElement = null;
	private hiddenText: HTMLDivElement = null;
	private isCollapsed: boolean = false;
	public multiFields: MultiField[] = [];

	public get multi(): boolean { return true; }

	protected getRowContainer(): HTMLDivElement {
		if(this.multiFieldContainerElement == null) this.buildMultiFieldContainer();
		return this.multiFieldContainerElement;
	}
	
	private createMultifield(): ModelSubfield {
		return new ModelSubfield(
			this.name,
			this.rowName,
			this.type,
			this.properties
		);
	}

	private buildNewMultifield(): ModelSubfield {

		// create row for button to right of field
		const multiRow = document.createElement("div") as HTMLDivElement;
		multiRow.classList.add(multiFieldRowStyle);

		// create field
		const fieldContainer = document.createElement("div") as HTMLDivElement;
		fieldContainer.classList.add(multiFieldPartStyle);
		const field = this.createMultifield() as MultiField;
		field.buildInterface(fieldContainer, false, this.readOnly);

		// use the requirement object for the multifield instead of each part 
		// having its own requirement
		field.requirement.destroy();
		field.requirement = this.requirement;

		// create button for removing the field entry
		const removeButton = document.createElement("button") as HTMLButtonElement;
		removeButton.type = "button";
		removeButton.innerHTML = faCloseIcon;

		// remove on click
		field.destroyRow = () => {
			const fieldIndex = this.multiFields.indexOf(field);
			this.multiFields.splice(fieldIndex, 1);
			field.destroy();
			multiRow.remove();
			this.requirement.applyRequirementWarningStyles();
		}
		removeButton.addEventListener("click", field.destroyRow);

		// add elements to root node
		this.multiFields.push(field);
		multiRow.appendChild(fieldContainer);
		if(!this.readOnly) multiRow.appendChild(removeButton);
		this.getRowContainer().appendChild(multiRow);

		return field;
	}

	private buildMultiFieldContainer(): void {

		// this has the potential to be built multiple times so its important 
		// to check it hasn't already been built
		if(this.multiFieldContainerElement != null) return;
		
		this.controlContainerElement = document.createElement("div");
		this.containerElement.appendChild(this.controlContainerElement);

		this.multiFieldContainerElement = document.createElement("div");
		this.multiFieldContainerElement.classList.add(multiFieldContainerStyle)
		this.controlContainerElement.appendChild(this.multiFieldContainerElement);

	}

	private buildNewItemButton(): void{
		this.newItemButton = document.createElement("button");
		this.newItemButton.type = "button";
		this.newItemButton.innerText = "+ add";
		this.newItemButton.addEventListener(
			"click", () => this.onNewItemPressed()
		);
		this.controlContainerElement.appendChild(this.newItemButton);
	}

	private onNewItemPressed(): void {
		this.buildNewMultifield();
	}

	public fillMultiFields(data: JSONArray, notify: boolean = true): void {
		this.clearMultifields();
		for(let i = 0; i < data.length; i++){
			const value = data[i];
			this.addNewMultifieldWithValue(value, notify);
		}
	}

	public clearMultifields(): void {
		for(const field of this.multiFields.toReversed()){
			field.destroyRow();
		}
		this.multiFields.length = 0;
	}

	public expandMultiFields(): void {
		for(const field of this.multiFields){
			field.expandSubfields();
		}
		this.expandField();
	}

	public collapseMultiFields(): void {
		for(const field of this.multiFields){
			field.collapseSubfields();
		}
	}

	public addNewMultifieldWithValue(value: JSONValue, notify: boolean = false): ModelSubfield {
		const field = this.buildNewMultifield();
		field.fillField(value, notify);
		return field;
	}

	public collapseField() {
		if(this.isCollapsed) return;
		this.collapseMultiFields();

		this.multiFieldContainerElement.style.overflow = "hidden";
		this.multiFieldContainerElement.style.maxHeight = "0";
		if(this.newItemButton) this.newItemButton.style.display = "none";
		this.hideButton.innerText = "show";

		this.hiddenText.style.display = "block";
		this.isCollapsed = true;
	}

	public expandField(){
		if(!this.isCollapsed) return;

		this.multiFieldContainerElement.style.removeProperty("max-height");
		this.multiFieldContainerElement.style.removeProperty("overflow");
		if(this.newItemButton) this.newItemButton.style.display = "block";
		this.hideButton.innerText = "hide";

		this.hiddenText.style.display = "none";
		this.isCollapsed = false;
	}

	private buildHideButton() {
		const hideButton = document.createElement('button');
		this.hideButton = hideButton;

		hideButton.innerText = "hide";
		hideButton.type = "button";
		hideButton.addEventListener("click", () => {
			if(this.isCollapsed) this.expandField();
			else this.collapseField();
		});
		this.labelElement.appendChild(hideButton);

		const hiddenText = document.createElement('div');
		this.hiddenText = hiddenText;
		hiddenText.innerText = "-- hidden --";
		hiddenText.style.display = "none";

		if(this.newItemButton) this.newItemButton.parentElement.appendChild(hiddenText);
	}

	/// Overriden funcitonality ------------------------------------------------

	public override buildInterface(
		targetDiv: HTMLDivElement, 
		buildFieldInfo: boolean = true,
		readOnly: boolean = false,
		condensed: boolean = false,
	): void {
		this.readOnly = readOnly;
		this.condensed = condensed;
		this.containerElement = document.createElement("div");

		if(buildFieldInfo) this.buildFieldInfo();
		this.buildMultiFieldContainer();
		this.buildNewMultifield();
		if(!readOnly) this.buildNewItemButton();
		this.buildHideButton();

		targetDiv.appendChild(this.containerElement);

		this.requirement = new FieldRequirement(
			this, this.properties.requirementLevel ?? RequirementLevel.OPTIONAL
		);
		this.requirement.containerElement = this.controlContainerElement;
		for(const field of this.multiFields){
			field.requirement = this.requirement;
		}
	}

	public override applyValidityStyles(): void {
		if(this.requirement == null) return;
		this.requirement.applyRequirementWarningStyles();
		for(const multifield of this.multiFields){
			for(const subfield of multifield.getSubfields()){
				subfield.applyValidityStyles();
			}
		}
	}

	public override expandSubfields(): void {
		super.expandSubfields();
		this.expandMultiFields();
	}

	public override collapseSubfields(): void {
		super.collapseSubfields();
		this.collapseMultiFields();
	}

	public override destroy(): void {
		super.destroy();
		this.multiFields.length = 0;
		this.multiFieldContainerElement = null;
		this.newItemButton = null;
	}

	public override clearField(): void {
		this.clearMultifields();
		this.requirement.removeStyles();
	}

	public override hasValidInput(): boolean {
		let hasAnyInput = false;
		for(const field of this.multiFields){
			if(!field.hasValidInput()) return false;
			hasAnyInput = true;
		}
		return hasAnyInput;
	}

	public override getFieldData(): { [key: string]: any; } | string | any[] {
		const arr: any[] = [];
		for(const field of this.multiFields) {
			const fieldVal = field.getFieldData();
			if(fieldVal != null && fieldVal !== "") arr.push(fieldVal);
		}
		return arr;
	}
	
	public override getInputElement(): AnyInputElement {
		for(let i = 1; i >= 0; i--) {
			for(const field of this.multiFields) {
				const input = field.getInputElement();
				if(input){
					if(i > 0 && input.validationMessage.length <= 0) continue;
					return input;
				}
			}
		}
		return null;
	}
}
