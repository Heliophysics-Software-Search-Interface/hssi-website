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

	public override refreshItems(): void {
		super.refreshItems();
		
		// parent the python items to a single python item
		const pythonSearch = (
			(item: ControlledListItem) => 
				(item as ControlledListItem).name.toLowerCase().includes("python")
		);
		const pythonIndex = this.rootItems.findIndex(pythonSearch as any);
		const pythonItems = this.rootItems.filter(pythonSearch as any);
		const pythonProxyItem = pythonItems[0] as ControlledListItem;
		const pythonRootItem = new ControlledListItem(
			this, 
			structuredClone(pythonProxyItem.objectData)
		);
		pythonRootItem.objectData.id = "";
		pythonRootItem.name = "Python";
		pythonRootItem.abbreviation = "Pyth";
		this.rootItems.splice(pythonIndex, 0, pythonRootItem);
		for(const pyItem of pythonItems){
			this.rootItems.splice(this.rootItems.indexOf(pyItem), 1);
			pythonRootItem.subItems.push(pyItem);
		}

		// parent the fortran items to a single fortran item
		const fotranSearch = (
			(item: ControlledListItem) => 
				(item as ControlledListItem).name.toLowerCase().includes("fortran")
		);
		const fortranIndex = this.rootItems.findIndex(fotranSearch as any);
		const fortranItems = this.rootItems.filter(fotranSearch as any);
		const fortranProxyItem = fortranItems[0] as ControlledListItem;
		const fortranRootItem = new ControlledListItem(
			this, 
			structuredClone(fortranProxyItem.objectData)
		);
		fortranRootItem.objectData.id = "";
		fortranRootItem.name = "Fortran";
		fortranRootItem.abbreviation = "Fort";
		this.rootItems.splice(fortranIndex, 0, fortranRootItem);
		for(const foItem of fortranItems){
			this.rootItems.splice(this.rootItems.indexOf(foItem), 1);
			fortranRootItem.subItems.push(foItem);
		}

		console.log(this.rootItems)
	}
}