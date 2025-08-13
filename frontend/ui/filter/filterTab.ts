import {
	SimpleEvent, fetchTimeout, FilterItem, CategoryItem,
	type JSONArray, type JSONObject, type JSONValue,
	FilterMenu,
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

const styleTabHeader = "tab-header";
const styleTabContent = "tab-content";

const styleVertical = "vertical";
const styleMenu = "menu";
const styleDropdown = "dropdown";
const styleAccordionMenu = "accordion-menu";
const styleMobileMenuContainer = "mobile-menu-container";

export class FilterTab {

	/** the selectable header for the tab */
	public headerElement: HTMLDivElement = null; // TODO

	/** contains elements for filter items and structure */
	public contentContainerElement: HTMLDivElement = null;

	/** contains filter item elements */
	public itemContainerElement: HTMLUListElement = null;

	/** the name of the database model to fetch the filter items from */
	public targetModel: string = "";

	/** a list of filter items to be displayed directly (not as children of other items) */
	public rootItems: FilterItem[] = [];

	/** all filter items that are currently selected by the user */
	public selectedItems: FilterItem[] = [];

	protected parentMenu: FilterMenu = null;
	protected isDropdown: boolean = false;
	protected modelData: JSONArray = [];

	/** event is fired when html elements are built and ready for display */
	public onReady: SimpleEvent = new SimpleEvent();

	/** text that is shown for the tab header */
	public get headerText(): string { return this.targetModel; }

	public constructor(parentMenu: FilterMenu){
		this.contentContainerElement = document.createElement("div");
		this.contentContainerElement.classList.add(styleTabContent);
		this.headerElement = document.createElement("div");
		this.headerElement.classList.add(styleTabHeader);
		this.parentMenu = parentMenu;
	}

	/** 
	 * start building html display elements for the tab, when ready
	 * {@link FilterTab.onReady} will be triggered
	 */
	public build(): void {
		this.fetchModelData().then(() => {
			this.refreshItems();
			this.rebuildHeaderElement();
			this.rebuildContentElements();
			this.onReady.triggerEvent();
		});
	}

	/**
	 * hide or show the tab contents (does not affect header visibility)
	 * @param visible whether the contents are visible or not
	 */
	public setContentsVisible(visible: boolean): void {
		const displayMode = visible ? "block" : "none";
		this.contentContainerElement.style.display = displayMode;
	}

	/** whether the specified data should be stored as a root filter item */
	protected itemDataValid(itemData: JSONValue): boolean { return true; }

	/** create a new root filter item for the tab */
	protected createItem(itemData: JSONValue): FilterItem {
		return new FilterItem(this, itemData);
	}

	/** recreate root filter items from db model data */
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

	/** rebuild the html element that displays the header */
	public rebuildHeaderElement(): void {
		this.headerElement.innerHTML = this.headerText;
		this.headerElement.addEventListener("click", () => {
			this.parentMenu.selectTab(this);
		});
	}

	/** rebuild html display elements for all items and content structure */
	public rebuildContentElements(): void {
		while (this.contentContainerElement.childNodes.length > 0){
			this.contentContainerElement.childNodes[0].remove();
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
		this.contentContainerElement.appendChild(this.itemContainerElement);

		// build items and add their html elements
		for(const item of this.rootItems){
			item.build();
			this.itemContainerElement.appendChild(item.containerElement);
		}
	}

	private async fetchModelData(): Promise<void> {
		const url = apiModel + this.targetModel + apiSlugRowsAll;
		const data = await fetchTimeout(url);
		const jsonData = await data.json();
		this.modelData = jsonData.data;
	}
}

export class CategoryFilterTab extends FilterTab{

	public get headerText(): string { return "Categories"; }

	public get categories(): CategoryItem[] { return this.rootItems as CategoryItem[]; }
	public get categoryData(): JSONArray<JSONObject> { 
		return this.modelData as JSONArray<JSONObject>; 
	}

	public constructor(parentMenu: FilterMenu) {
		super(parentMenu);
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
