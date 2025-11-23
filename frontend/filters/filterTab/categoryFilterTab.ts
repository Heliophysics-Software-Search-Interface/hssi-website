import { 
	ControlledListFilterTab, 
	CategoryItem, 
	FilterMenu,
	FilterMenuItem,
	type JSONValue,
	type JSONArray,
	type JSONObject
} from "../../loader";

export class CategoryFilterTab extends ControlledListFilterTab {

	public get headerText(): string { return "Functionality"; }

	public get categories(): CategoryItem[] { return this.rootItems as CategoryItem[]; }
	public get categoryData(): JSONArray<JSONObject> { 
		return this.modelData as JSONArray<JSONObject>; 
	}

	public constructor(parentMenu: FilterMenu) {
		super(parentMenu);
		this.targetModel = "FunctionCategory";
		this.targetField = "softwareFunctionality";
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
