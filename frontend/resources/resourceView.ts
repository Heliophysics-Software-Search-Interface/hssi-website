import { 
	apiModel, apiSlugRowsAll, extractDoi, fetchTimeout, HssiModelDataAsync, isUuid4, modelApiUrl, ModelData, ModelDataCache, ResourceItem, 
	SimpleEvent, 
	Spinner, 
	styleHidden, 
	type JSONArray, type JSONObject, type SoftwareData,
	type SoftwareDataAsync,
} from "../loader";

const styleNoResults = "no-results";
const softwarModelName = "VisibleSoftware";
const idResourceContainer = "resource_content";

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
	public refreshItems(): void {

		// remove all old items
		for(const oldItem of this.items) oldItem.destroy();
		this.items.length = 0;

		// create new items from data
		for(const data of this.itemData) {
			if(this.specificUids != null) {
				if(!(this.specificUids.includes(data.id.toLowerCase()))) continue;
			}
			const item = ResourceItem.createFromData(data);
			this.containerElement.appendChild(item.containerElement);
			this.items.push(item);
		}

		// display no results if no results found, or hide it if there is results
		if(this.items.length <= 0) this.noResourcesElem.classList.remove(styleHidden);
		else this.noResourcesElem.classList.add(styleHidden);
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
	public showItems(items: SoftwareDataAsync[]): void {
		const prevData = this.itemData;
		this.itemData = items;
		this.refreshItems();
		this.itemData = prevData;
	}

	/** 
	 * fetch item data from the server and build items from the 
	 * data received 
	 */
	public async fetchAndBuild(): Promise<void> {

		Spinner.showSpinner("Fetching Software Data...", this.containerElement);

		if(this.specificUids){
			this.itemData = [...await (
				ModelDataCache.getModelData("VisibleSoftware", this.specificUids) as any
			)];
		}
		else this.itemData = [...await ModelDataCache.getModelDataAll("VisibleSoftware")];

		this.onReady.triggerEvent();

		this.refreshItems();
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
}

// expose to global
const win = window as any;
win.makeResourceView = makeResourceView;
