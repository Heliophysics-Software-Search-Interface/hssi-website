/**
 * The "Data Source" tab, filtering `data_sources` by `DataInput`. Touch this
 * when changing which model or software field the tab filters.
 *
 * @module
 */

import { 
	ControlledListFilterTab,
	FilterMenu,
} from "../../loader";

/** The "Data Source" tab, filtering `data_sources` by `DataInput`. */
export class DataSourcesFilterTab extends ControlledListFilterTab {

	/** Overrides to return `"Data Source"`. */
	public get headerText(): string { return "Data Source"; }

	/** Sets the target model and field. */
	public constructor(parentMenu: FilterMenu) {
		super(parentMenu);
		this.targetModel = "DataInput";
		this.targetField = "data_sources";
	}
}