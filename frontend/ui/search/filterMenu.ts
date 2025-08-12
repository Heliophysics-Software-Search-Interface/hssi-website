import {
	SimpleEvent, fetchTimeout,
	type JSONArray, type JSONObject, type JSONValue,
} from "../../loader";

/**
 * This module aims to reproduce the html structure below for each individual 
 * function category - or for a more generalized approach - to each individual 
 * row in a controlled list model:
 * 
 * <li class="filter_menu">
 * 	<a class="filter_dropdown"> 
 * 		<div class="filter_label">
 * 			<label 
 * 				class="label {{tag.abbreviation}}" 
 * 				style="background-color: {{tag.backgroundColor}}; color: {{tag.textColor}}"
 *			>
 * 				<input 
 * 					class="label {{tag.abbreviation}} parent_filter" 
 * 					type="checkbox" name="{{filter_type}}_checkbox" 
 * 					value="{{tag.id}}" id="{{tag.id}}"
 * 					{% if tag.id in selected_filter_ids %} checked {% endif %} 
 * 				>
 * 					{{tag.abbreviation}}
 * 			</label>
 * 			<label 
 *				for="{{tag.id}}" 
 *				class="category_name {{tag.abbreviation}}" 
 *				parent-abbr="{{tag.abbreviation}}"
 *			>
 *				{{tag.name}}
 *			</label> 
 * 		</div>
 * 	</a>
 * 	<ul>
 * 		{% for subtag in tag.functionalities.all %}
 * 		<li style="list-style: none;">
 * 			<div style="display: flex; align-items: center; white-space: nowrap; overflow: hidden;">
 * 			</div>
 * 			<input class="label sub_filter" type="checkbox" 
 * 				name="{{filter_type}}_checkbox" value="{{subtag.id}}" 
 * 				id="{{tag.id}}_{{subtag.id}}"
 * 				{% if subtag.id in selected_subfilter_ids %} checked {% endif %} 
 * 			>
 * 			<label class="subcategory_name" for="{{tag.id}}_{{subtag.id}}"> 
 * 				{{ subtag.name }} 
 * 			</label>
 * 		</li>
 * 		{% endfor %}
 * 	</ul>
 * </li>
 */

const apiModel = "/api/models/";
const apiSlugRowsAll = "/rows/all/";
const styleFilterTable = "filter_table";
const styleVertical = "vertical";
const styleMenu = "menu";
const styleDropdown = "dropdown";
const styleAccordionMenu = "accordion-menu";
const styleMobileMenuContainer = "mobile-menu-container";
const styleFilterMenu = "filter_menu";
const styleFilterDropdown = "filter_dropdown";
const styleFilterLabel = "filter_label";
const styleLabel = "label";
const styleParentFilter = "label";
const styleCategoryName = "category_name";
const styleSubFilter = "sub_filter";
const styleSubcategoryName = "subcategory_name";

export class FilterMenu {

	public containerElement: HTMLDivElement = null;
	public itemContainerElement: HTMLUListElement = null;
	public targetModel: string = "";
	public rootItems: FilterMenuItem[] = [];
	public selectedItems: FilterMenuItem[] = [];
	protected isDropdown: boolean = false;
	protected modelData: JSONArray = [];

	public onReady: SimpleEvent = new SimpleEvent();

	public constructor(isDropdown: boolean){
		this.containerElement = document.createElement("div");
		this.isDropdown = isDropdown;
	}

	public build(): void {
		this.fetchModelData().then(() => {
			this.refreshItems();
			this.rebuildElements();
			this.onReady.triggerEvent();
		});
	}

	private async fetchModelData(): Promise<void> {
		const url = apiModel + this.targetModel + apiSlugRowsAll;
		const data = await fetchTimeout(url);
		const jsonData = await data.json();
		console.log("fetched model objects:", jsonData.data);
		this.modelData = jsonData.data;
	}

	protected itemDataValid(itemData: JSONValue): boolean { return true; }

	protected createItem(itemData: JSONValue): FilterMenuItem {
		return new FilterMenuItem(this, itemData);
	}

	public refreshItems(): void {
		for(const item of this.rootItems) item.destroy();
		this.rootItems.length = 0;
		for(const itemData of this.modelData){
			if(this.itemDataValid(itemData)){
				const item = this.createItem(itemData);
				this.rootItems.push(item);
			}
		}
	}

	public rebuildElements(): void {
		while (this.containerElement.childNodes.length > 0){
			this.containerElement.childNodes[0].remove();
		}
		
		// apply styles to item container
		this.itemContainerElement = document.createElement("ul");
		this.itemContainerElement.classList.add(styleVertical);
		this.itemContainerElement.classList.add(styleMenu);
		this.itemContainerElement.classList.add(styleAccordionMenu);
		if(this.isDropdown){
			this.itemContainerElement.classList.add(styleDropdown);
			this.itemContainerElement.classList.add(styleMobileMenuContainer);
		}
		this.itemContainerElement.setAttribute("data-accordion-menu", "");
		this.containerElement.appendChild(this.itemContainerElement);

		// build items and add their html elements
		for(const item of this.rootItems){
			item.build();
			this.itemContainerElement.appendChild(item.containerElement);
		}
	}
}

class CategoryFilterMenu extends FilterMenu{

	public get categories(): CategoryItem[] { return this.rootItems as CategoryItem[]; }
	public get categoryData(): JSONArray<JSONObject> { 
		return this.modelData as JSONArray<JSONObject>; 
	}

	public constructor(dropdown: boolean) {
		super(dropdown);
		this.targetModel = "FunctionCategory";
	}

	protected override itemDataValid(itemData: JSONValue): boolean {
		const data = itemData as JSONObject;
		if(data?.parents instanceof Array) return data.parents.length <= 0;
		return true;
	}

	protected override createItem(itemData: JSONValue): FilterMenuItem {
		const category = new CategoryItem(this, itemData);
		const data = itemData as JSONObject;

		// find and parse direct children
		if(data?.children instanceof Array){
			for(const uid of data.children){
				const id = uid as string;
				const childData = this.categoryData.find(x => { return x.id == id; });
				if(childData){
					category.children.push(new CategoryItem(this, childData));
				}
			}
		}

		return category;
	}
}

export class FilterMenuItem {

	protected parentMenu: FilterMenu = null;
	public containerElement: HTMLLIElement = null;
	public labelElement: HTMLElement = null;
	public subContainerElement: HTMLUListElement = null;
	public subItems: FilterMenuItem[] = [];
	protected data: JSONValue = null;

	public get label(): string { return this.data.toString(); }

	public constructor(parent: FilterMenu, data: JSONValue) {
		this.parentMenu = parent;
		this.containerElement = document.createElement("li");
		this.containerElement.classList.add(styleFilterMenu);
		this.data = data;
	}

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
		
		// add information regarding ids and abbreviations here so we don't 
		// need to override in subclass
		if (this.data instanceof Object){
			if((this.data as any).id){
				checkbox.value = (this.data as any).id;
				checkbox.id = (this.data as any).id;
			}
			if((this.data as any).abbreviation){
				labelName.setAttribute("parent-abbr", (this.data as any).abbreviation);
				checkbox.classList.add((this.data as any).abbreviation);
				labelAbbr.append((this.data as any).abbreviation);
			}
		}
		
		this.subContainerElement = document.createElement('ul');
		this.containerElement.appendChild(this.subContainerElement);

		// build subItem children html elements
		for(const child of this.subItems) {
			this.buildChildItem(child);
			this.subContainerElement.appendChild(child.containerElement);
		}
	}

	public buildChildItem(child: FilterMenuItem){

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

	public destroy(): void {
		for(const sub of this.subItems) sub.destroy();
		this.subItems.length = 0;
		this.containerElement.remove();
	}
}

class ControlledListItem extends FilterMenuItem {
	public get objectData(): JSONObject { return this.data as JSONObject; }
	public get id(): string { return this.objectData.id as any; }
	public get name(): string { return this.objectData.name as any; }
	public get identifier(): string { return this.objectData.identifier as any; }
}

class GraphListItem extends ControlledListItem {
	public get childData(): JSONArray<JSONObject> { 
		return this.objectData.children as any; 
	}
	public get parentData(): JSONArray<JSONObject> {
		return this.objectData.parents as any;
	}
}

class CategoryItem extends GraphListItem {
	public get bgColor(): string { return this.objectData.backgroundColor as any; }
	public get textColor(): string { return this.objectData.textColor as any; }
	public get children(): CategoryItem[] { return this.subItems as any; }
	public get label(): string { return this.objectData.name as any; }
}

export function makeFilterMenuElement(dropdown: boolean): void {
	const categoriesMenu = new CategoryFilterMenu(dropdown);
	const scriptElement = document.currentScript;
	categoriesMenu.onReady.addListener(() => {
		scriptElement.parentNode.appendChild(categoriesMenu.containerElement);
	});
	categoriesMenu.build();
}

// export functionality to global scope
const win = window as any;
win.makeFilterMenuElement = makeFilterMenuElement;