/**
 * The "Phenomena" tab, filtering `related_phenomena` by `Phenomena`. Not
 * currently added to the filter menu. Touch this when changing which model or
 * software field the tab filters.
 *
 * @module
 */

import { 
	ControlledListFilterTab,
	FilterMenu,
} from "../../loader";

/**
 * The "Phenomena" tab, filtering `related_phenomena` by `Phenomena`. Not
 * currently added to the filter menu.
 */
export class PhenomenaFilterTab extends ControlledListFilterTab {

	/** Overrides to return `"Phenomena"`. */
	public get headerText(): string { return "Phenomena"; }

	/** Sets the target model and field. */
	public constructor(parentMenu: FilterMenu) {
		super(parentMenu);
		this.targetModel = "Phenomena";
		this.targetField = "related_phenomena";
	}
}