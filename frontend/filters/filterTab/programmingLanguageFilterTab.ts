/**
 * The "Prog. Language" tab, filtering `programming_language` by
 * `ProgrammingLanguage`. Touch this when changing which model or software field
 * the tab filters.
 *
 * @module
 */

import { 
	ControlledListFilterTab, 
	ControlledListItem, 
	FilterMenu,
} from "../../loader";

/**
 * The "Prog. Language" tab, filtering `programming_language` by
 * `ProgrammingLanguage`.
 */
export class ProgrammingLanguageFilterTab extends ControlledListFilterTab {
	
	/** Overrides to return `"Prog. Language"`. */
	public get headerText(): string { return "Prog. Language"; }

	/** Sets the target model and field. */
	public constructor(parentMenu: FilterMenu) {
		super(parentMenu);
		this.targetModel = "ProgrammingLanguage";
		this.targetField = "programming_language";
	}

	/**
	 * Overrides to group all Python and all Fortran variants under a single
	 * "Python" and "Fortran" parent item each.
	 */
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
	}
}