import { 
	colorSrcGreen,
	ControlledListFilterTab, 
	ControlledListItem, 
	FilterMenu,
	FilterMenuItem,
	type JSONValue
} from "../../loader";

export class ProgrammingLanguageFilterTab extends ControlledListFilterTab {
	
	public get headerText(): string { return "Prog. Languages"; }

	public get categories(): ControlledListItem[] { 
		return this.rootItems as ControlledListItem[]; 
	}

	public constructor(parentMenu: FilterMenu) {
		super(parentMenu);
		this.targetModel = "ProgrammingLanguage";
	}

	protected override createItem(itemData: JSONValue): FilterMenuItem {
		const item = new ControlledListItem(this, itemData);

		switch(item.name.toLowerCase()){
			case "javascript": item.abbreviation = "JaSc"; break;
			case "typescript": item.abbreviation = "TySc"; break;
			case "fortran77": item.abbreviation = "Fo77"; break;
			case "fortran90": item.abbreviation = "Fo90"; break;
			default:
				let splname = item.name.replaceAll(".", "").split(" ");
				switch(splname.length){
					case 2: 
					item.abbreviation = (
						splname[0].substring(0, 2) + 
						splname[1].substring(splname[1].length - 2, splname[1].length)
					);
					break;
					default:
						item.abbreviation = item.name.substring(0, 4);
						break;
				}
				break;
		}
				
		return item;
	}
}