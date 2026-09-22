import { 
	apiModel, apiSlugRowsAll, extractDoi, fetchTimeout, HssiModelDataAsync, isUuid4, modelApiUrl, ModelData, ModelDataCache, ResourceItem, 
	SimpleEvent, 
	Spinner, 
	styleHidden, 
	type JSONArray, type JSONObject, type SoftwareData,
	type SoftwareDataAsync,
} from "../loader";

const styleNoResults = "no-results";
const stylePageControls = "page-controls";
const softwarModelName = "VerifiedSoftware";
const idResourceContainer = "resource_content";
type ResourceSort = "date" | "create" | "name";

function resourceSortFromUrl(): ResourceSort {
	const value = new URLSearchParams(window.location.search).get("sort");
	return value === "create" || value === "name" ? value : "date";
}

/** 
 * a list-style display that shows users different software resource entries 
 * from within the HSSI database
 */
export class ResourceView {

	private static mainInstance: ResourceView = null;
	public static onMainViewCreated: SimpleEvent = new SimpleEvent();

	private noResourcesElem: HTMLDivElement = null;
	private specificUids: string[] = null;
	private parentElement: HTMLElement = null;
	private itemData: SoftwareDataAsync[] = [];
	private items: ResourceItem[] = [];
	private paginatedMode: boolean = false;
	private paginationOffset: number = 0;
	private paginationTotal: number = 0;
	private paginationControlsEl: HTMLDivElement = null;
	private readonly PAGE_SIZE = 25;
	private sort: ResourceSort = resourceSortFromUrl();

	public onReady: SimpleEvent = null;

	private static resourceViewMap: Map<HTMLElement, ResourceView> = new Map();

	/** 
	 * Gets the main resource view element that updates according to 
	 * search queries 
	 */
	public static get main(): ResourceView {
		return this.mainInstance;
	}

	/** Get the resource view on a specific element if it exists */
	public static getViewInElement(element: HTMLElement){
		return ResourceView.resourceViewMap.get(element)
	}

	public setParentElement(element: HTMLElement) {
		if(this.parentElement) ResourceView.resourceViewMap.delete(this.parentElement);
		if(element) ResourceView.resourceViewMap.set(element, this);
		this.parentElement = element;
	}

	/** the html element that contains all the html content for this view */
	public containerElement: HTMLDivElement = null;

	public constructor() {
		if(!ResourceView.mainInstance) {
			ResourceView.mainInstance = this;
			ResourceView.onMainViewCreated.triggerEvent();
		}

		this.onReady = new SimpleEvent();
		this.containerElement = document.createElement("div");
		this.containerElement.style.minHeight = "100px";

		this.noResourcesElem = document.createElement("div");
		this.noResourcesElem.classList.add(styleNoResults, styleHidden);
		this.noResourcesElem.innerHTML = (
			"No resources match your search...yet!<br/>"+
			"Would you like to <a href='/submit'>submit a new resource?</a>"
		);

		this.containerElement.appendChild(this.noResourcesElem);
		this.buildPaginationControls();
		this.updateSortControls();
		document.querySelectorAll<HTMLButtonElement>("#sort_menu .sort-button").forEach(button => {
			button.addEventListener("click", () => {
				this.setSort(button.dataset.sort as ResourceSort);
			});
		});
	}

	private updateSortControls(): void {
		const hasSearch = !!new URLSearchParams(window.location.search).get("q")?.trim();
		const menu = document.getElementById("sort_menu");
		const count = this.paginatedMode ? this.paginationTotal : this.items.length;
		if (menu) menu.hidden = hasSearch || count === 0;
		document.querySelectorAll<HTMLButtonElement>("#sort_menu .sort-button").forEach(button => {
			const active = button.dataset.sort === this.sort;
			button.classList.toggle("active-sort", active);
			button.setAttribute("aria-pressed", String(active));
		});
	}

	public updateResultHeader(): void {
		const count = this.paginatedMode ? this.paginationTotal : this.items.length;
		const label = document.getElementById("result-count");
		if (label) label.textContent = `Showing ${count} ${count === 1 ? "resource" : "resources"}.`;
		this.updateSortControls();
	}

	private sortItems(items: SoftwareDataAsync[]): SoftwareDataAsync[] {
		const sorted = [...items];
		const nameOrder = (a: SoftwareDataAsync, b: SoftwareDataAsync) =>
			a.software_name.localeCompare(b.software_name, undefined, { sensitivity: "base" });
		if (this.sort === "name") return sorted.sort(nameOrder);
		const field = this.sort === "create" ? "publication_date" : "metadata_modified_date";
		return sorted.sort((a, b) => {
			const first = a[field] || "";
			const second = b[field] || "";
			if (!first) return second ? 1 : nameOrder(a, b);
			if (!second) return -1;
			return second.localeCompare(first) || nameOrder(a, b);
		});
	}

	private async setSort(sort: ResourceSort): Promise<void> {
		if (sort === this.sort) return;
		this.sort = sort;
		const url = new URL(window.location.href);
		if (sort === "date") url.searchParams.delete("sort");
		else url.searchParams.set("sort", sort);
		url.searchParams.delete("page");
		history.pushState(null, "", url);
		this.paginationOffset = 0;
		this.updateSortControls();
		if (this.paginatedMode) await this.loadPage(0, false);
		else this.refreshItems();
	}

	private buildPaginationControls(): void {
		this.paginationControlsEl = document.createElement("div");
		this.paginationControlsEl.classList.add(stylePageControls);
		this.paginationControlsEl.classList.add(styleHidden);
		this.containerElement.appendChild(this.paginationControlsEl);
	}

	private updatePaginationControls(): void {
		if (!this.paginationControlsEl) return;
		this.paginationControlsEl.innerHTML = "";
		if (!this.paginatedMode) {
			this.paginationControlsEl.classList.add(styleHidden);
			return;
		}
		const currentPage = Math.floor(this.paginationOffset / this.PAGE_SIZE) + 1;
		const totalPages = Math.ceil(this.paginationTotal / this.PAGE_SIZE) || 1;

		const prevBtn = document.createElement("button");
		prevBtn.textContent = "← Previous";
		prevBtn.disabled = this.paginationOffset === 0;
		prevBtn.addEventListener("click", () => this.loadPage(this.paginationOffset - this.PAGE_SIZE));

		const pageIndicator = document.createElement("span");
		pageIndicator.textContent = `Page ${currentPage} of ${totalPages}`;

		const nextBtn = document.createElement("button");
		nextBtn.textContent = "Next →";
		nextBtn.disabled = this.paginationOffset + this.PAGE_SIZE >= this.paginationTotal;
		nextBtn.addEventListener("click", () => this.loadPage(this.paginationOffset + this.PAGE_SIZE));

		this.paginationControlsEl.appendChild(prevBtn);
		this.paginationControlsEl.appendChild(pageIndicator);
		this.paginationControlsEl.appendChild(nextBtn);
		this.paginationControlsEl.classList.remove(styleHidden);
	}

	private recordPageUrlParam(push: boolean = true): void {
		const page = Math.floor(this.paginationOffset / this.PAGE_SIZE) + 1;
		const newUrl = new URL(window.location.href);
		if (page <= 1) newUrl.searchParams.delete("page");
		else newUrl.searchParams.set("page", String(page));
		if (push) history.pushState(null, "", newUrl);
	}

	private async loadPage(offset: number, pushHistory: boolean = true): Promise<void> {
		if (offset < 0 || offset >= this.paginationTotal) return;
		Spinner.showSpinner("Loading...", this.containerElement);
		this.paginationOffset = offset;
		const { items, total } = await ModelDataCache.fetchPage(softwarModelName, offset, this.PAGE_SIZE, this.sort);
		this.itemData = items;
		this.paginationTotal = total;
		this.specificUids = null;
		this.refreshItems();
		this.updatePaginationControls();
		if (pushHistory) this.recordPageUrlParam();
		this.containerElement.scrollIntoView({ behavior: "smooth" });
		Spinner.hideSpinner(this.containerElement);
	}

	/** restore the correct page when the user navigates back/forward */
	public async onPopState(): Promise<void> {
		const previousSort = this.sort;
		this.sort = resourceSortFromUrl();
		this.updateSortControls();
		if (!this.paginatedMode) {
			if (this.sort !== previousSort) this.refreshItems();
			return;
		}
		const pageParam = new URLSearchParams(window.location.search).get("page");
		const page = Math.max(1, parseInt(pageParam || "1", 10));
		const offset = (page - 1) * this.PAGE_SIZE;
		if (offset === this.paginationOffset && this.sort === previousSort) return;
		await this.loadPage(offset, false);
	}

	/** load all software data and exit paginated mode; no-op if already in full mode */
	public async awaitAllItems(): Promise<void> {
		if (!this.paginatedMode && ModelDataCache.getCache(softwarModelName).hasFetchedAllData) return;
		const allItems = [...await ModelDataCache.getModelDataAll(softwarModelName)];
		this.itemData = allItems;
		this.paginatedMode = false;
		this.updatePaginationControls();
	}

	/** return to page 0 of paginated mode; no-op if already paginated */
	public async resetToPaginatedMode(): Promise<void> {
		if (this.paginatedMode) return;
		this.paginatedMode = true;
		this.paginationOffset = 0;
		const { items, total } = await ModelDataCache.fetchPage(softwarModelName, 0, this.PAGE_SIZE, this.sort);
		this.itemData = items;
		this.paginationTotal = total;
		this.updatePaginationControls();
	}

	/** clear any active uid filter so all loaded items are shown */
	public clearFilter(): void {
		this.specificUids = null;
	}

	/** get all item data that is loaded for the resource view */
	public getAllItems(): SoftwareDataAsync[] {
		return this.itemData;
	}

	/** get only the items that are currently displayed in the resource view */
	public getActiveItems(): SoftwareDataAsync[] {
		return this.items.map(itm => itm.softwareData);
	}

	/** 
	 * gets only the items included in the specific uuid set for the 
	 * resource view 
	 */
	public getFilteredItems(): SoftwareDataAsync[] {
		if(!this.specificUids) return this.getAllItems();
		const items: SoftwareDataAsync[] = [];
		for (const item of this.getAllItems()){
			if(this.specificUids.includes(item.id)) items.push(item);
		}
		return items;
	}

	/** create new items based on stored item data */
	public refreshItems(preserveOrder: boolean = false): void {

		// remove all old items
		for(const oldItem of this.items) oldItem.destroy();
		this.items.length = 0;

		// create new items from data
		const dataToShow = preserveOrder || this.paginatedMode ? this.itemData : this.sortItems(this.itemData);
		for(const data of dataToShow) {
			if(this.specificUids != null) {
				if(!(this.specificUids.includes(data.id.toLowerCase()))) continue;
			}
			const item = ResourceItem.createFromData(data);
			this.containerElement.appendChild(item.containerElement);
			this.items.push(item);
		}

		// keep pagination controls at the bottom
		if (this.paginationControlsEl) this.containerElement.appendChild(this.paginationControlsEl);

		// display no results if no results found, or hide it if there is results
		if(this.items.length <= 0) this.noResourcesElem.classList.remove(styleHidden);
		else this.noResourcesElem.classList.add(styleHidden);
		this.updateResultHeader();
	}

	/** 
	 * restrict the resource view to show only softwares with these 
	 * specific uids 
	 */
	public filterToItems(uids: string[]): void{
		if(uids != null) {
			for(const uid of uids) {
				if(!isUuid4(uid)) throw new Error(`${uid} is not a valid UID`);
			}
		}
		this.specificUids = uids.map(s => s.toLowerCase());
	}

	/** shows only the specified items in the resource view */
	public showItems(items: SoftwareDataAsync[], preserveOrder: boolean = false): void {
		const prevData = this.itemData;
		this.itemData = items;
		this.refreshItems(preserveOrder);
		this.itemData = prevData;
	}

	/** 
	 * fetch item data from the server and build items from the 
	 * data received 
	 */
	public async fetchAndBuild(): Promise<void> {

		Spinner.showSpinner("Fetching Software Data...", this.containerElement);

		if (this.specificUids) {
			this.itemData = [...await (
				ModelDataCache.getModelData(softwarModelName, this.specificUids) as any
			)];
		} else {
			const urlParams = new URLSearchParams(window.location.search);
			const hasSearch = urlParams.has("q");
			const hasFilter = urlParams.has("filt");
			if (!hasSearch && !hasFilter) {
				this.paginatedMode = true;
				const pageParam = urlParams.get("page");
				const initialPage = Math.max(1, parseInt(pageParam || "1", 10));
				this.paginationOffset = (initialPage - 1) * this.PAGE_SIZE;
				const { items, total } = await ModelDataCache.fetchPage(softwarModelName, this.paginationOffset, this.PAGE_SIZE, this.sort);
				this.itemData = items;
				this.paginationTotal = total;
			} else {
				this.itemData = [...await ModelDataCache.getModelDataAll(softwarModelName)];
			}
		}

		this.onReady.triggerEvent();

		this.refreshItems();
		this.updatePaginationControls();
		Spinner.hideSpinner(this.containerElement);
	}
}

function makeResourceView(uids: string[]) {
	const node = document.currentScript.parentNode as HTMLElement;
	const view = new ResourceView();

	// show only specified uids if given
	if(uids) view.filterToItems(uids);

	node.appendChild(view.containerElement);
	view.setParentElement(node);
	view.fetchAndBuild();

	window.addEventListener("popstate", () => view.onPopState());
}

// expose to global
const win = window as any;
win.makeResourceView = makeResourceView;
