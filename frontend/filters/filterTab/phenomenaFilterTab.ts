import { 
	ControlledListFilterTab,
	FilterMenu,
} from "../../loader";

export class PhenomenaFilterTab extends ControlledListFilterTab {

	public get headerText(): string { return "Phenomena"; }

	public constructor(parentMenu: FilterMenu) {
		super(parentMenu);
		this.targetModel = "Phenomena";
		this.targetField = "relatedPhenomena";
	}
}