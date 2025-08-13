import { 
	FilterMenuItem 
} from "../../loader";

const styleFilterContainer = "filter-container";
const styleInvertFilter = "invert-filter";

enum FilterGroupMode {
	Or = 0,
	And = 1,
}

export class FilterGroupMaker {

	private chipContainerElement: HTMLDivElement = null;
	private controlsContainerElement: HTMLDivElement = null;
	private chips: ItemChip[] = [];

	/** the html element that acts as a container for all display elements */
	public containerElement: HTMLDivElement = null;

	public constructor(){
		this.containerElement = document.createElement("div");
	}

	/** 
	 * build the html elements that represent the filter group maker and 
	 * controls 
	 */
	public build(): void {
		this.chipContainerElement = document.createElement("div");
		this.chipContainerElement.classList.add(styleFilterContainer);
		this.chipContainerElement.append("Filters: ")
		this.containerElement.appendChild(this.chipContainerElement);

		this.controlsContainerElement = document.createElement("div");
		this.containerElement.appendChild(this.controlsContainerElement);
	}

	/** 
	 * add the specified filter item to the group list (if its not already
	 * included), to be made into part of the filter group 
	 */
	public addItem(item: FilterMenuItem): void {

		// ensure item is not already included
		const index = this.chips.findIndex(
			chip => { return chip.itemReference == item; }
		);
		if(index >= 0) return;

		// add item and visuals
		const chip = new ItemChip(item);
		chip.build();
		this.chipContainerElement.appendChild(chip.chip);
		this.chips.push(chip);
	}

	/**
	 * remove the specified filter item so it does not get included in the 
	 * group when created
	 */
	public removeItem(item: FilterMenuItem): void {
		const index = this.chips.findIndex(
			chip => { return chip.itemReference == item; }
		);
		if(index < 0) return;
		this.chips[index].destroy();
		this.chips.splice(index, 1);
	}

	/** remove all filter items */
	public clearItems(): void {
		for(const chip of this.chips) chip.destroy();
		this.chips.length = 0;
	}

	/** creates a {@link FilterGroup} from the items included in the group list */
	public createGroup(): FilterGroup {
		const group = new FilterGroup();
		// TODO
		return null;
	}
}

export class FilterGroup {
	
	/** items that are to be included in the query results */
	public includedItems: FilterMenuItem[] = [];

	/** items that are to be excluded from the query results */
	public excludedItems: FilterMenuItem[] = [];

	public mode: FilterGroupMode = FilterGroupMode.Or;

	/** create a small display element that represents the whole filter group */
	public createChip(): HTMLSpanElement{
		const span = document.createElement("span");
		for(const inc of this.includedItems){
			const chip = inc.createChip();
			span.appendChild(chip);
		}
		for(const exc of this.excludedItems){
			const chip = exc.createChip();
			chip.classList.add(styleInvertFilter);
			span.appendChild(chip);
		}
		return span;
	}
}

class ItemChip {
	public itemReference: FilterMenuItem = null;
	public chip: HTMLSpanElement = null;
	public filterInverted: boolean = false;

	public constructor(item: FilterMenuItem){
		this.itemReference = item;
	}

	public build(): void {
		this.chip = this.itemReference.createChip();
		// TODO add x button
	}

	public destroy(): void {
		this.chip.remove();
	}
}