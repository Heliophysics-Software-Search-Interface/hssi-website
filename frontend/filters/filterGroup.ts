import { 
	faCloseIcon,
	FilterMenu, FilterMenuItem,
	GraphListItem,
	SimpleEvent,
	styleSelected,
} from "../loader";

const styleFilterContainer = "filter-container";
const styleFilterControls = "filter-controls";
const styleInvertFilter = "invert-filter";
const styleGroupControl = "group-control";
const styleGroupClear = "group-clear";
const styleGroupCreate = "group-create";
const styleGroupMode = "group-mode";

enum FilterGroupMode {
	Or = 0,
	And = 1,
}

export class FilterGroupMaker {

	private parentMenu: FilterMenu = null;
	private chipContainerElement: HTMLDivElement = null;
	private controlsContainerElement: HTMLDivElement = null;
	private chips: ItemChip[] = [];
	private currentMode: FilterGroupMode = FilterGroupMode.Or;

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

		const modeAnd = document.createElement("button");
		modeAnd.classList.add(styleGroupControl);
		modeAnd.classList.add(styleGroupMode);
		modeAnd.innerText = "AND";
		this.controlsContainerElement.appendChild(modeAnd);
		
		const modeOr = document.createElement("button");
		modeOr.classList.add(styleGroupControl);
		modeOr.classList.add(styleGroupMode);
		modeOr.classList.add(styleSelected);
		modeOr.innerText = "OR";
		this.controlsContainerElement.appendChild(modeOr);

		modeOr.addEventListener("click", e => {
			this.currentMode = FilterGroupMode.Or;
			modeOr.classList.add(styleSelected);
			modeAnd.classList.remove(styleSelected);
		});
		modeAnd.addEventListener("click", e => {
			this.currentMode = FilterGroupMode.And;
			modeAnd.classList.add(styleSelected);
			modeOr.classList.remove(styleSelected);
		});
		
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
			const group = this.createGroup();
			// TODO apply filter group 
		})

		this.setControlsVisible(false);
	}

	/** 
	 * add the specified filter item to the group list (if its not already
	 * included), to be made into part of the filter group 
	 */
	public async addItem(item: FilterMenuItem): Promise<void> {

		// ensure item is not already included
		const index = this.chips.findIndex(
			chip => { return chip.itemReference == item; }
		);
		if(index >= 0) return;

		// add item and visuals
		const chip = new ItemChip(item);
		await chip.build();
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
		group.mode = this.currentMode;
		
		for (const chip of this.chips){
			const item = chip.itemReference;
			if(!chip.filterInverted) group.includedItems.push(item);
			else group.excludedItems.push(item);
		}
		
		this.clearItems();
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
	public async createChip(): Promise<HTMLSpanElement>{
		const span = document.createElement("span");
		for(const inc of this.includedItems){
			const chip = await inc.createChip();
			span.appendChild(chip);
		}
		for(const exc of this.excludedItems){
			const chip = await exc.createChip();
			chip.classList.add(styleInvertFilter);
			span.appendChild(chip);
		}
		return span;
	}
}

class ItemChip {
	public itemReference: FilterMenuItem = null;
	public chip: HTMLSpanElement = null;
	public removeButton: HTMLButtonElement = null;
	public filterInverted: boolean = false;

	public constructor(item: FilterMenuItem){
		this.itemReference = item;
	}

	private setInverted(inverted: boolean): void {
		this.filterInverted = inverted;
		if(inverted) this.chip.classList.add(styleInvertFilter);
		else this.chip.classList.remove(styleInvertFilter);
	}

	public async build(): Promise<void> {
		this.chip = await this.itemReference.createChip();
		this.chip.addEventListener("click", e => {
			this.setInverted(!this.filterInverted);
		});
		this.chip.title = "Click to invert condition";

		// create 'remove' button
		this.removeButton = document.createElement("button");
		this.removeButton.innerHTML = faCloseIcon;
		this.removeButton.addEventListener("click", e => {
			this.itemReference.parentMenu.setItemSelected(
				this.itemReference, false
			);
		});
		this.chip.appendChild(this.removeButton);
	}

	public destroy(): void {
		this.chip.remove();
	}
}