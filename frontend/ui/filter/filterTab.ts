import {
	SimpleEvent, fetchTimeout, FilterItem, CategoryItem,
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

export class FilterTab {

	public containerElement: HTMLDivElement = null;
	public itemContainerElement: HTMLUListElement = null;
	public targetModel: string = "";
	public rootItems: FilterItem[] = [];
	public selectedItems: FilterItem[] = [];
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

	protected createItem(itemData: JSONValue): FilterItem {
		return new FilterItem(this, itemData);
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

export class CategoryFilterTab extends FilterTab{

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

	protected override createItem(itemData: JSONValue): FilterItem {
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

export function makeFilterMenuElement(dropdown: boolean): void {
	const categoriesMenu = new CategoryFilterTab(dropdown);
	const scriptElement = document.currentScript;
	categoriesMenu.onReady.addListener(() => {
		scriptElement.parentNode.appendChild(categoriesMenu.containerElement);
	});
	categoriesMenu.build();
}

// export functionality to global scope
const win = window as any;
win.makeFilterMenuElement = makeFilterMenuElement;