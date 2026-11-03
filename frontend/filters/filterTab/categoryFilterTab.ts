/**
 * The "Functionality" tab, filtering `software_functionality` by
 * `FunctionCategory`. Touch this when changing which model or software field
 * the tab filters.
 *
 * @module
 */

import { 
	ControlledListFilterTab, 
	CategoryItem, 
	FilterMenu,
	FilterMenuItem,
	type JSONValue,
	type JSONArray,
	type JSONObject
} from "../../loader";

/**
 * The "Functionality" tab, filtering `software_functionality` by
 * `FunctionCategory`.
 */
export class CategoryFilterTab extends ControlledListFilterTab {

	/** Overrides to return `"Functionality"`. */
	public get headerText(): string { return "Functionality"; }

	/** The root items as `CategoryItem`s. */
	public get categories(): CategoryItem[] { return this.rootItems as CategoryItem[]; }
	/** The model data as JSON objects. */
	public get categoryData(): JSONArray<JSONObject> { 
		return this.modelData as JSONArray<JSONObject>; 
	}

	/** Sets the target model and field. */
	public constructor(parentMenu: FilterMenu) {
		super(parentMenu);
		this.targetModel = "FunctionCategory";
		this.targetField = "software_functionality";
	}

	/** Overrides so only categories without parents become root items. */
	protected override itemDataValid(itemData: JSONValue): boolean {
		const data = itemData as JSONObject;
		if(data?.parents instanceof Array) return data.parents.length <= 0;
		return true;
	}

	/**
	 * Overrides to create a `CategoryItem` with its direct child categories as
	 * sub-items.
	 */
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
