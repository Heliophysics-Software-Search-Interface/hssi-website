import {
	FieldRequirement, ModelSubfield,
	RequirementLevel,
} from "../loader";

const multiFieldRowStyle = "multi-field-row";
const multiFieldPartStyle = "multi-field-part";
const multiFieldContainerStyle = "multifield-container";

/**
 * A special type of {@link ModelSubfield} which can be used to dynamically 
 * allow users to add multiple entries of the same type to a field
 */
export class ModelMultiSubfield extends ModelSubfield {

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

		// use the requirement object for the multifield instead of each part 
		// having its own requirement
		field.requirement.destroy();
		field.requirement = this.requirement;

		// create button for removing the field entry
		const removeButton = document.createElement("button") as HTMLButtonElement;
		removeButton.type = "button";
		removeButton.innerHTML = "<i class='fa fa-close'></i>";

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
}