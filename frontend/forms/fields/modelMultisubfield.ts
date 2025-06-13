import {
	FieldRequirement, ModelSubfield,
	RequirementLevel,
	type AnyInputElement,
	type JSONArray,
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
	private multiFields: MultiField[] = [];
	private newItemButton: HTMLButtonElement = null;

	public get multi(): boolean { return true; }

	protected getRowContainer(): HTMLDivElement {
		if(this.multiFieldContainerElement == null) this.buildMultiFieldContainer();
		return this.multiFieldContainerElement;
	}
	
	private createMultifield(): ModelSubfield {
		return new ModelSubfield(
			this.name, 
			this.type, 
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
		const field = this.createMultifield() as MultiField;
		field.buildInterface(fieldContainer, false);

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
		multiRow.appendChild(removeButton);
		this.getRowContainer().appendChild(multiRow);
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

	public fillMultiFields(data: JSONArray): void {
		this.clearMultifields();
		for(let i = 0; i < data.length; i++){
			const value = data[i];
			this.buildNewMultifield();
			this.multiFields[i].fillField(value);
		}
	}

    /// Overriden funcitonality ------------------------------------------------

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

		this.requirement = new FieldRequirement(
			this, this.properties.requirementLevel ?? RequirementLevel.OPTIONAL
		);
		this.requirement.containerElement = this.controlContainerElement;
		for(const field of this.multiFields){
			field.requirement = this.requirement;
		}
	}

	public applyValidityStyles(): void {
		if(this.requirement == null) return;
		this.requirement.applyRequirementWarningStyles();
		for(const multifield of this.multiFields){
			for(const subfield of multifield.getSubfields()){
				subfield.applyValidityStyles();
			}
		}
	}

	public clearMultifields(): void {
		for(const field of this.multiFields){
			field.destroyRow();
		}
		this.multiFields.length = 0;
	}

	public destroy(): void {
		super.destroy();
		this.multiFields.length = 0;
		this.multiFieldContainerElement = null;
		this.newItemButton = null;
	}

	public hasValidInput(): boolean {
		for(const field of this.multiFields){
			if(field.hasValidInput()) return true;
		}
		return false;
	}

	public getFieldData(): { [key: string]: any; } | string | any[] {
		const arr: any[] = [];
		for(const field of this.multiFields) {
			const fieldVal = field.getFieldData();
			if(fieldVal != null && fieldVal !== "") arr.push(fieldVal);
		}
		return arr;
	}
	
	public getInputElement(): AnyInputElement {
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
