import {
	SimpleEvent, fetchTimeout,
	type JSONArray ,
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
 * 				<input class="label {{tag.abbreviation}} parent_filter" 
 * 				type="checkbox" name="{{filter_type}}_checkbox" 
 * 				value="{{tag.id}}" id="{{tag.id}}"
 * 				{% if tag.id in selected_filter_ids %} checked {% endif %} >
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
const styleFilterMenu = "filter_menu";
const styleFilterDropdown = "filter_dropdown";
const styleFilterLabel = "filter_label";
const styleLabel = "label";
const styleCategoryName = "category_name";
const styleSubFilter = "sub_filter";
const styleSubcategoryName = "subcategory_name";

export class FilterMenu{

	public containerElement: HTMLDivElement = null;
	private targetModel: string = "";
	private items: FilterMenuItem[] = [];
	private modelData: JSONArray = [];

	public onReady: SimpleEvent = new SimpleEvent();

	private constructor(){
		this.containerElement = document.createElement("div");
	}

	private async fetchModelData(): Promise<void> {
		const url = apiModel + this.targetModel + apiSlugRowsAll;
		const data = await fetchTimeout(url);
		const jsonData = await data.json();
		console.log("fetched model objects:", jsonData.data);
		this.modelData = jsonData.data;
	}

	public refreshItems(): void {
		for(const item of this.items) item.destroy();
		this.items.length = 0;
		// TODO
	}

	public rebuildElements(): void {
		while (this.containerElement.childNodes.length > 0){
			this.containerElement.childNodes[0].remove();
		}
		// TODO
	}

	public static CreateCategories(): FilterMenu {
		const r = new FilterMenu();
		r.targetModel = "FunctionCategory";
		r.fetchModelData().then(() => {
			r.refreshItems();
			r.rebuildElements();
			r.onReady.triggerEvent();
		});
		return r;
	}
}

export class FilterMenuItem{

	public containerElement: HTMLLIElement = null;
	private subItems: FilterMenuItem[] = [];

	private constructor() {
		this.containerElement = document.createElement("li");
	}

	public destroy(): void {
		// TODO
	}

	public static Create(): FilterMenuItem {
		const r = new FilterMenuItem();
		return r;
	}
}

export function makeFilterMenuElement(): void {
	const categoriesMenu = FilterMenu.CreateCategories();
	categoriesMenu.onReady.addListener(() => {
		document.currentScript.parentNode.appendChild(
			categoriesMenu.containerElement
		);
	});
}

// export functionality to global scope
const win = window as any;
win.makeFilterMenuElement = makeFilterMenuElement;