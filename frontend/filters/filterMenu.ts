import { 
	FilterTab, CategoryFilterTab, FilterMenuItem, FilterGroupMaker,
	ProgrammingLanguageFilterTab,
	FilterGroup,
	ResourceView,
	faCloseIcon,
	filterGroupToUrlVal,
	type SoftwareDataAsync,
	urlValToFilterGroup,
} from "../loader";

export const styleHidden = "hidden";
export const styleSelected = "selected";
const styleFilterMenu = "filter-menu";
const styleTabContainer = "tab-container";
const styleFilterGroupContainer = "active-filters";
const urlSymGroupDelimiter = "..";
const searchParamFilter = "filt";

export class FilterMenu {
	
	private static mainInstance: FilterMenu = null;
	public static get main(): FilterMenu { return this.mainInstance; }

	private activeGroupsContainerElement: HTMLDivElement = null;
	private groupMaker: FilterGroupMaker = null;
	private curTab: FilterTab = null;
	private selectedItems: FilterMenuItem[] = [];
	private activeFilterGroups: FilterGroup[] = [];
	private targetView: ResourceView = null;

	/** contains all elements for menu */
	public containerElement: HTMLDivElement = null;
	public tabHeadersElement: HTMLDivElement = null;
	public tabContentsElement: HTMLDivElement = null;

	/** all filter tabs that are selectable in the menu */
	public tabs: FilterTab[] = [];

	/** the tab that is currently selected by the user */
	public get currentTab(): FilterTab { return this.curTab; }

	public constructor(view: ResourceView) {
		this.containerElement = document.createElement("div");
		this.containerElement.classList.add(styleFilterMenu);

		if(!FilterMenu.mainInstance) {
			FilterMenu.mainInstance = this;
			window.addEventListener("popstate", _ => { this.parseUrlParams(); } );
		}

		// TODO make this less stupid
		if(view == null){
			window.addEventListener("DOMContentLoaded", e => {
				this.targetView = ResourceView.getMainView();
			});
		}
		else this.targetView = view;
	}

	private attachRemoveButton(chip: HTMLSpanElement, group: FilterGroup) {
		const removeButton = document.createElement("button");
		removeButton.innerHTML = faCloseIcon;
		removeButton.addEventListener("click", _ => {
			const index = this.activeFilterGroups.indexOf(group);
			if(index >= 0){
				this.activeFilterGroups.splice(index, 1);
				this.applyFilters();
			}
		});
		chip.appendChild(removeButton);
	}

	private async parseUrlParams(): Promise<void> {
		const search = new URLSearchParams(window.location.search);
		const groupVals = search.get(searchParamFilter)?.split(urlSymGroupDelimiter);
		
		this.activeFilterGroups.length = 0;
		if(!groupVals) {
			this.applyFilters(false);
			return;
		}

		for(const groupval of groupVals) {
			const group = await urlValToFilterGroup(groupval);
			this.addFilterGroup(group);
		}

		try{
			this.applyFilters(false);
		}
		catch{
			window.addEventListener("DOMContentLoaded", _ => this.applyFilters());
		}
	}

	/** build all display html elements for the {@link FilterMenu} */
	public build(): void {

		// clear tab content and headers
		for(const node of this.containerElement.childNodes) node.remove();

		this.groupMaker = new FilterGroupMaker(this);
		this.containerElement.appendChild(this.groupMaker.containerElement);
		this.groupMaker.build();

		this.groupMaker.onItemRemoved.addListener(item => {
			this.setItemSelected(item, false);
		});

		// active filter group container
		this.activeGroupsContainerElement = document.createElement("div");
		this.activeGroupsContainerElement.classList.add(styleFilterGroupContainer);
		this.activeGroupsContainerElement.classList.add(styleHidden);
		this.activeGroupsContainerElement.append("Active Filter Groups: ");
		this.containerElement.appendChild(this.activeGroupsContainerElement);

		// tab headers
		this.tabHeadersElement = document.createElement("div");
		this.tabHeadersElement.classList.add(styleTabContainer);
		this.containerElement.appendChild(this.tabHeadersElement);
		
		this.tabContentsElement = document.createElement("div");
		this.containerElement.appendChild(this.tabContentsElement);

		// build tab html elements
		for(const tab of this.tabs){
			tab.build();
			this.tabHeadersElement.appendChild(tab.headerElement);
			this.tabContentsElement.appendChild(tab.contentContainerElement);
		}

		// hide all tab contents except the current tab
		for(const tab of this.tabs) tab.setContentsVisible(false);
		this.selectTab(this.tabs[0]);

		// get active filter groups from url
		this.parseUrlParams();
	}

	/** set the current tab to the specified tab and update contents */
	public selectTab(tab: FilterTab): void {
		if(this.curTab == tab) return;
		if(this.curTab) {
			this.curTab.setContentsVisible(false);
			this.curTab.headerElement.classList.remove(styleSelected);
		}
		this.curTab = tab;
		if(tab){
			tab.headerElement.classList.add(styleSelected);
			tab.setContentsVisible(true);
		}
	}

	/** 
	 * marks a specific filter item as being selected or not by the user, so 
	 * that it will be considered when a filter group is made
	 * @param item the item to select/deselect
	 * @param selected whether or not the item is marked as selected
	 */
	public setItemSelected(item: FilterMenuItem, selected: boolean): void {
		if(this.selectedItems.includes(item) == selected) return;

		if(selected) {
			this.groupMaker.addItem(item);
			this.selectedItems.push(item);
			item.checkboxElement.checked = true;
			item.containerElement.classList.add(styleSelected);
		}
		else {
			this.groupMaker.removeItem(item);
			this.selectedItems.splice(this.selectedItems.indexOf(item), 1);
			item.checkboxElement.checked = false;
			item.containerElement.classList.remove(styleSelected);
		}
	}

	/** returns the tab that filters the specified software field */
	public getTabForField(field: keyof SoftwareDataAsync): FilterTab {
		return this.tabs.find(tab => tab.targetField == field);
	}

	public addFilterGroup(group: FilterGroup): void {
		this.activeFilterGroups.push(group);
	}

	/** Apply all the active filter groups to the results */
	public applyFilters(pushHistory: boolean = true): void {

		// clear old chips
		this.activeGroupsContainerElement.innerHTML = "Active Filter Groups: ";
		
		let items = this.targetView.getAllItems();
		for(const group of this.activeFilterGroups){
			items = group.filterSoftware(items);

			// render chips
			const chip = group.createChip();
			this.activeGroupsContainerElement.append(chip);
			this.attachRemoveButton(chip, group);
		}
		this.targetView.filterToItems(items.map(item => item.id));
		this.targetView.refreshItems();

		// show/hide active groups element
		if (this.activeFilterGroups.length > 0){
			this.activeGroupsContainerElement.classList.remove(styleHidden);
		}
		else this.activeGroupsContainerElement.classList.add(styleHidden);

		// if it's the main view, we'll want to append the filters as url params
		if(this.targetView == ResourceView.getMainView()){
			if(pushHistory) this.recordFilterUrlParams();
		}
	}

	private recordFilterUrlParams(): void {

		let filterParamVal = "";
		for(const group of this.activeFilterGroups){
			filterParamVal += filterGroupToUrlVal(group) + urlSymGroupDelimiter;
		}

		// chop off the last delimiter
		if(filterParamVal.length > 0) {
			filterParamVal = filterParamVal.substring(
				0, 
				filterParamVal.length - urlSymGroupDelimiter.length
			);
		}

		// Record filter to browser history
		const newUrl = new URL(window.location.href);
		if (filterParamVal) newUrl.searchParams.set(searchParamFilter, filterParamVal);
		else newUrl.searchParams.delete(searchParamFilter);
		history.pushState(null, "", newUrl);
	}
}

export function makeFilterMenuElement(targetView: ResourceView = null): void {
	const view = targetView || ResourceView.getMainView();
	const filterMenu = new FilterMenu(view);
	filterMenu.tabs.push(new CategoryFilterTab(filterMenu));
	filterMenu.tabs.push(new ProgrammingLanguageFilterTab(filterMenu));
	document.currentScript.parentNode.appendChild(filterMenu.containerElement);
	filterMenu.build();
}

// export functionality to global scope
const win = window as any;
win.makeFilterMenuElement = makeFilterMenuElement;
win.FilterMenu = FilterMenu;