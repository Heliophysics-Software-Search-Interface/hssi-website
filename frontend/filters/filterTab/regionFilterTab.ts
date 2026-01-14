import { 
	ControlledListFilterTab,
	FilterMenu,
} from "../../loader";

export class RegionFilterTab extends ControlledListFilterTab {

	public get headerText(): string { return "Region"; }

	public constructor(parentMenu: FilterMenu) {
		super(parentMenu);
		this.targetModel = "Region";
		this.targetField = "relatedRegion";
	}
}