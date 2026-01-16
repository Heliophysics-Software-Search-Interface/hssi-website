import { 
	ControlledListFilterTab,
	FilterMenu,
} from "../../loader";

export class DataSourcesFilterTab extends ControlledListFilterTab {

	public get headerText(): string { return "Data Source"; }

	public constructor(parentMenu: FilterMenu) {
		super(parentMenu);
		this.targetModel = "DataInput";
		this.targetField = "dataSources";
	}
}