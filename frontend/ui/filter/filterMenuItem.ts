import {
	SimpleEvent, FilterTab,
	type JSONArray, type JSONObject, type JSONValue,
} from "../../loader";


const textCollapse = "▲";
const textExpand = "▼";
const styleFilterItem = "filter-item";
const styleFilterSubItem = "filter-sub-item";
const styleSubItemList = "filter-sub-list";
const styleItemChip = "item-chip";
const styleSubchip = "subchip";

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
export class FilterMenuItem {

	protected parentMenu: FilterTab = null;
	protected data: JSONValue = null;
	private expandButton: HTMLButtonElement = null;
	private parentItem: FilterMenuItem = null;

	/** a unique UUID representing the filter item */
	public get id(): string { return (this.data as any)?.id; }

	/** html element that contains all other elements of the item */
	public containerElement: HTMLLIElement = null;

	/** element that holds the display text */
	public labelElement: HTMLElement = null;

	/** element that user interacts with */
	public checkboxElement: HTMLInputElement = null;

	/** element that contains child items */
	public subContainerElement: HTMLUListElement = null;

	/** list of items that are children of this element */
	public subItems: FilterMenuItem[] = [];

	/** triggered when the item has children and is expanded to show them */
	public onExpand: SimpleEvent = new SimpleEvent();

	/** the label text that the item displays as in the label element */
	public get labelString(): string { return this.data.toString(); }

	/** whether or not the subitems are expanded and visible */
	public get isExpanded(): boolean { 
		return (this.subContainerElement?.style?.display ?? "none") != "none"; 
	}

	public constructor(parent: FilterTab, data: JSONValue) {
		this.parentMenu = parent;
		this.containerElement = document.createElement("li");
		this.containerElement.classList.add(styleFilterMenu);
		this.containerElement.classList.add(styleFilterItem);
		this.data = data;
	}

	/** 
	 * create a small display element that can be used to represent this item 
	 * anywhere in the document
	 */
	public createChip(): HTMLSpanElement {
		const chip = document.createElement("span");
		chip.classList.add(styleLabel);
		chip.classList.add(styleItemChip);
		if(this.parentItem) chip.classList.add(styleSubchip);
		chip.innerText = this.labelString.substring(0,4);
		return chip;
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
		
		this.checkboxElement = document.createElement("input");
		this.checkboxElement.classList.add(styleLabel);
		this.checkboxElement.classList.add(styleParentFilter);
		this.checkboxElement.type = "checkbox";
		this.checkboxElement.name = this.parentMenu.targetModel + "_checkbox";
		if(this.parentMenu.selectedItems.includes(this)) this.checkboxElement.checked = true;
		labelDiv.appendChild(this.checkboxElement);
		
		const chip = this.createChip();
		labelDiv.appendChild(chip);

		const name = document.createElement("span");
		name.classList.add(styleCategoryName);
		name.innerText = this.labelString;
		labelDiv.appendChild(name);
				
		this.subContainerElement = document.createElement("ul");
		this.subContainerElement.classList.add(styleSubItemList);
		this.containerElement.appendChild(this.subContainerElement);

		// build dropdown button only if there are subitems
		if (this.subItems.length > 0) {
			this.expandButton = document.createElement("button");
			this.expandButton.type = "button";
			labelDiv.appendChild(this.expandButton);
			this.expandButton.addEventListener("click", e => {
				this.setSubitemsExpanded(!this.isExpanded);
			});
			this.setSubitemsExpanded(false);
		}

		// build subItem children html elements
		for(const child of this.subItems) {
			this.buildChildItem(child);
			this.subContainerElement.appendChild(child.containerElement);
		}
	}

	/** creates all elements that represent an item who is a child of this */
	public buildChildItem(child: FilterMenuItem){
		child.parentItem = this;
		child.build();
		child.containerElement.classList.add(styleFilterSubItem);
	}

	/** remove the item's html elements from the DOM and destroy children */
	public destroy(): void {
		for(const sub of this.subItems) sub.destroy();
		this.subItems.length = 0;
		this.containerElement.remove();
	}

	public setSubitemsExpanded(expand: boolean): void {
		if(this.isExpanded === expand) return;
		const text = expand ? textCollapse : textExpand;
		this.expandButton.innerText = text;
		this.subContainerElement.style.display = expand ? "block" : "none";
	}
}

export class ControlledListItem extends FilterMenuItem {
	public get objectData(): JSONObject { return this.data as JSONObject; }
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
	public get labelString(): string { return this.objectData.name as any; }

	public override createChip(): HTMLSpanElement {
		let chip = super.createChip();
		chip.style.backgroundColor = this.bgColor;
		chip.style.borderColor = this.bgColor;
		chip.style.color = this.textColor;
		chip.innerText = this.abbreviation;
		return chip;
	}

	public override build(): void {
		super.build();

		this.checkboxElement.value = this.id;
		this.checkboxElement.id = this.id;
		this.checkboxElement.classList.add(this.abbreviation);

		const name = 
			this.containerElement
			.querySelector(`span.${styleCategoryName}`);
		name.setAttribute("for", this.id);
		name.setAttribute("parent-abbr", this.abbreviation);
		name.classList.add(this.abbreviation);
	
	}
}
