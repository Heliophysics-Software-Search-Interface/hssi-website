import {
	SimpleEvent, fetchTimeout, FilterTab,
	type JSONArray, type JSONObject, type JSONValue,
} from "../../loader";

const styleFilterMenu = "filter_menu";
const styleFilterDropdown = "filter_dropdown";
const styleFilterLabel = "filter_label";
const styleLabel = "label";
const styleParentFilter = "label";
const styleCategoryName = "category_name";
const styleSubFilter = "sub_filter";
const styleSubcategoryName = "subcategory_name";

/**
 * represents a selectable item in a filter menu tab, also incorpoerates 
 * shallow single level graph depth for root items and child items which are
 * both selectable and distinct
 */
export class FilterItem {

	protected parentMenu: FilterTab = null;
	protected data: JSONValue = null;

	/** html element that contains all other elements of the item */
	public containerElement: HTMLLIElement = null;

	/** element that holds the display text */
	public labelElement: HTMLElement = null;

	/** element that contains child items */
	public subContainerElement: HTMLUListElement = null;

	/** list of items that are children of this element */
	public subItems: FilterItem[] = [];

	/** the label text that the item displays as in the label element */
	public get label(): string { return this.data.toString(); }

	public constructor(parent: FilterTab, data: JSONValue) {
		this.parentMenu = parent;
		this.containerElement = document.createElement("li");
		this.containerElement.classList.add(styleFilterMenu);
		this.data = data;
	}

	/** creates all display html elements for the list item */
	public build(): void {

		// clear html elements
		while(this.containerElement.childNodes.length > 0){
			this.containerElement.childNodes[0].remove;
		}
		
		// build internal html elements
		this.labelElement = document.createElement('a');
		this.labelElement.classList.add(styleFilterDropdown);
		this.containerElement.appendChild(this.labelElement);

		const labelDiv = document.createElement("div");
		labelDiv.classList.add(styleFilterLabel);
		this.labelElement.appendChild(labelDiv);

		const labelAbbr = document.createElement("label");
		labelAbbr.classList.add(styleLabel);
		labelDiv.appendChild(labelAbbr);
		
		const checkbox = document.createElement("input");
		checkbox.classList.add(styleLabel);
		checkbox.classList.add(styleParentFilter);
		checkbox.type = "checkbox";
		checkbox.name = this.parentMenu.targetModel + "_checkbox";
		if(this.parentMenu.selectedItems.includes(this)) checkbox.checked = true;
		labelAbbr.appendChild(checkbox);
		
		const labelName = document.createElement("label");
		labelName.classList.add(styleCategoryName);
		labelName.innerText = this.label;
		labelDiv.appendChild(labelName);
				
		this.subContainerElement = document.createElement('ul');
		this.containerElement.appendChild(this.subContainerElement);

		// build subItem children html elements
		for(const child of this.subItems) {
			this.buildChildItem(child);
			this.subContainerElement.appendChild(child.containerElement);
		}
	}

	/** creates all elements that represent an item who is a child of this */
	public buildChildItem(child: FilterItem){

		// clear all child's internal html elements
		while(child.containerElement.childNodes.length > 0){
			child.containerElement.childNodes[0].remove();
		}

		const checkbox = document.createElement("input");
		checkbox.classList.add(styleLabel);
		checkbox.classList.add(styleSubFilter);
		checkbox.type = "checkbox";
		checkbox.name = this.parentMenu.targetModel + "_checkbox";
		if(this.parentMenu.selectedItems.includes(child)) checkbox.checked = true;
		child.containerElement.appendChild(checkbox);
		
		// add child id here if applicable, to avoid overriding in subclass
		if(child.data instanceof Object){
			if((child.data as any).id){
				checkbox.value = (child.data as any).id;
				checkbox.id = (child.data as any).id;
			}
		}

		child.labelElement = document.createElement("label");
		child.labelElement.classList.add(styleSubcategoryName);
		child.labelElement.innerText = child.label;
		child.containerElement.appendChild(child.labelElement);
	}

	/** remove the item's html elements from the DOM and destroy children */
	public destroy(): void {
		for(const sub of this.subItems) sub.destroy();
		this.subItems.length = 0;
		this.containerElement.remove();
	}
}

export class ControlledListItem extends FilterItem {
	public get objectData(): JSONObject { return this.data as JSONObject; }
	public get id(): string { return this.objectData.id as any; }
	public get name(): string { return this.objectData.name as any; }
	public get abbreviation(): string { return this.objectData.abbreviation as any; }
	public get identifier(): string { return this.objectData.identifier as any; }
}

export class GraphListItem extends ControlledListItem {
	public get childData(): JSONArray<JSONObject> { 
		return this.objectData.children as any; 
	}
	public get parentData(): JSONArray<JSONObject> {
		return this.objectData.parents as any;
	}
}

export class CategoryItem extends GraphListItem {
	public get bgColor(): string { return this.objectData.backgroundColor as any; }
	public get textColor(): string { return this.objectData.textColor as any; }
	public get children(): CategoryItem[] { return this.subItems as any; }
	public get label(): string { return this.objectData.name as any; }

	public build(): void {
		super.build();

		// add information regarding ids and abbreviations here so we don't 
		// need to override in subclass
		if (this.data instanceof Object){
			const checkbox = 
				this.containerElement
				.querySelector(`label input.${styleLabel}`) as HTMLInputElement;
			const labelName = 
				this.containerElement
				.querySelector(`label.${styleCategoryName}`);
			const labelAbbr = 
				this.containerElement
				.querySelector(`label.${styleLabel}`) as HTMLLabelElement;
			
			checkbox.value = this.id;
			checkbox.id = this.id;
			checkbox.classList.add(this.abbreviation);
			labelAbbr.classList.add(this.abbreviation);
			labelAbbr.append(this.abbreviation);
			labelAbbr.style.backgroundColor = this.bgColor;
			labelAbbr.style.color = this.textColor;
			labelName.setAttribute("for", this.id);
			labelName.setAttribute("parent-abbr", this.abbreviation);
			labelName.classList.add(this.abbreviation);
		}
	}
}
