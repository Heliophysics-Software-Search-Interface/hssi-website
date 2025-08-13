import { 
	FilterMenu, FilterMenuItem,
	SimpleEvent,
} from "../../loader";

const styleFilterContainer = "filter-container";
const styleFilterControls = "filter-controls";
const styleInvertFilter = "invert-filter";
const styleGroupControl = "group-control";
const styleGroupClear = "group-clear";
const styleGroupCreate = "group-create";

enum FilterGroupMode {
	Or = 0,
	And = 1,
}

export class FilterGroupMaker {

	private parentMenu: FilterMenu = null;
	private chipContainerElement: HTMLDivElement = null;
	private controlsContainerElement: HTMLDivElement = null;
	private chips: ItemChip[] = [];

	/** called whenever an item/chip is removed from the filter group maker */
	public onItemRemoved: SimpleEvent<FilterMenuItem> = new SimpleEvent();

	/** the html element that acts as a container for all display elements */
	public containerElement: HTMLDivElement = null;

	public constructor(menu: FilterMenu){
		this.parentMenu = menu;
		this.containerElement = document.createElement("div");
	}

	private setControlsVisible(visible: boolean): void {
		const visibleStr = visible ? "block" : "none";
		this.controlsContainerElement.style.display = visibleStr;
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
		this.controlsContainerElement.classList.add(styleFilterControls);
		this.containerElement.appendChild(this.controlsContainerElement);

		const clearFilters = document.createElement("button");
		clearFilters.classList.add(styleGroupControl);
		clearFilters.classList.add(styleGroupClear);
		clearFilters.innerText = "Clear";
		this.controlsContainerElement.appendChild(clearFilters);

		clearFilters.addEventListener("click", e => {
			this.clearItems();
		});

		const createGroup = document.createElement("button");
		createGroup.classList.add(styleGroupControl);
		createGroup.classList.add(styleGroupCreate);
		createGroup.innerText = "Apply";
		this.controlsContainerElement.appendChild(createGroup);

		createGroup.addEventListener("click", e => {
			this.createGroup();
		})

		this.setControlsVisible(false);
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
		this.setControlsVisible(true);
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
		if(this.chips.length <= 0) this.setControlsVisible(false);
	}

	/** remove all filter items */
	public clearItems(): void {

		// we need to iterate backwards because they may be removed as
		// iteration is happening
		for(let i = this.chips.length - 1; i >= 0; i--) {
			const chip = this.chips[i];
			chip.destroy();
			this.onItemRemoved.triggerEvent(chip.itemReference);
		}
		this.chips.length = 0;
		this.setControlsVisible(false);
	}

	/** creates a {@link FilterGroup} from the items included in the group list */
	public createGroup(): FilterGroup {
		const group = new FilterGroup();
		// TODO
		return group;
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