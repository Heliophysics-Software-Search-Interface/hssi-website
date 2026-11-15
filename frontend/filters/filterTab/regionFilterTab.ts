/**
 * The "Region" tab, filtering `related_region` by `Region`. Touch this when
 * changing which model or software field the tab filters.
 *
 * @module
 */

import { 
	ControlledListFilterTab,
	FilterMenu,
} from "../../loader";

/** The "Region" tab, filtering `related_region` by `Region`. */
export class RegionFilterTab extends ControlledListFilterTab {

	/** Overrides to return `"Region"`. */
	public get headerText(): string { return "Region"; }

	/** Sets the target model and field. */
	public constructor(parentMenu: FilterMenu) {
		super(parentMenu);
		this.targetModel = "Region";
		this.targetField = "related_region";
	}
}