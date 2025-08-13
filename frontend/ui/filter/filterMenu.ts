import { 
	FilterTab, CategoryFilterTab, FilterItem,
} from "../../loader";

const styleFilterMenu = "filter-menu";
const styleSelected = "selected";

export class FilterMenu {

	/** contains all elements for  */
	public containerElement: HTMLDivElement = null;
	public tabHeadersElement: HTMLDivElement = null;
	public tabContentsElement: HTMLDivElement = null;
	private curTab: FilterTab = null;
	private selectedItems: FilterItem[] = [];

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

		this.tabHeadersElement = document.createElement("div");
		this.tabContentsElement = document.createElement("div");
		this.containerElement.appendChild(this.tabHeadersElement);
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