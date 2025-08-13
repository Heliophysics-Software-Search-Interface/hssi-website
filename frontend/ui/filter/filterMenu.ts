import { 
	FilterTab, CategoryFilterTab, FilterMenuItem, FilterGroupMaker,
} from "../../loader";

const styleFilterMenu = "filter-menu";
const styleSelected = "selected";
const styleTabContainer = "tab-container";

export class FilterMenu {
	
	private groupMaker: FilterGroupMaker = null;
	private curTab: FilterTab = null;
	private selectedItems: FilterMenuItem[] = [];

	/** contains all elements for menu */
	public containerElement: HTMLDivElement = null;
	public tabHeadersElement: HTMLDivElement = null;
	public tabContentsElement: HTMLDivElement = null;

	/** all filter tabs that are selectable in the menu */
	public tabs: FilterTab[] = [];

	/** the tab that is currently selected by the user */
	public get currentTab(): FilterTab { return this.curTab; }

	public constructor() {
		this.containerElement = document.createElement("div");
		this.containerElement.classList.add(styleFilterMenu);
	}

	/** build all display html elements for the {@link FilterMenu} */
	public build(): void {

		// clear tab content and headers
		for(const node of this.containerElement.childNodes) node.remove();

		this.groupMaker = new FilterGroupMaker();
		this.containerElement.appendChild(this.groupMaker.containerElement);
		this.groupMaker.build();

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
}

export function makeFilterMenuElement(): void {
	const filterMenu = new FilterMenu();
	filterMenu.tabs.push(new CategoryFilterTab(filterMenu));
	document.currentScript.parentNode.appendChild(filterMenu.containerElement);
	filterMenu.build();
}

// export functionality to global scope
const win = window as any;
win.makeFilterMenuElement = makeFilterMenuElement;