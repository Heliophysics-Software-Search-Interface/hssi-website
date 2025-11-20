import { 
	apiModel, apiSlugRowsAll, extractDoi, fetchTimeout, isUuid4, modelApiUrl, ModelData, ModelDataCache, ResourceItem, 
	Spinner, 
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

	// TODO: manage element internally: 
	// No resources match your search...yet!<br/>
	// Would you like to 
	// 	<a href='/submit'>
	// 		submit a new resource?
	// 	</a>

	private specificUids: string[] = null;
	private parentElement: HTMLElement = null;
	private itemData: SoftwareDataAsync[] = [];
	private items: ResourceItem[] = [];
	
	private static resourceViewMap: Map<HTMLElement, ResourceView> = new Map();

	/** 
	 * Gets the main resource view element that updates according to 
	 * search queries 
	 */
	public static getMainView(): ResourceView {
		return ResourceView.getViewInElement(document.getElementById(idResourceContainer));
	}

	/** Get the resource view on a specific element if it exists */
	public static getViewInElement(element: HTMLElement){
		return ResourceView.resourceViewMap.get(element)
	}

	/** element to display when no results */
	private get noResultsElement(): HTMLElement {
		return document.body.getElementsByClassName(styleNoResults)[0] as any;
	}

	public setParentElement(element: HTMLElement) {
		if(this.parentElement) ResourceView.resourceViewMap.delete(this.parentElement);
		if(element) ResourceView.resourceViewMap.set(element, this);
		this.parentElement = element;
	}

	/** the html element that contains all the html content for this view */
	public containerElement: HTMLDivElement = null;

	public constructor() {
		this.containerElement = document.createElement("div");
		this.containerElement.style.minHeight = "100px";
	}

	/** create new items based on stored item data */
	public refreshItems(): void {

		// remove all old items
		for(const oldItem of this.items) oldItem.destroy();
		this.items.length = 0;

		// TODO implement filtering

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
		const noResultsElem = this.noResultsElement;
		if(noResultsElem){
			if(this.items.length <= 0) this.noResultsElement.style.display = "block";
			else this.noResultsElement.style.display = "none";
		}
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

	/** 
	 * fetch item data from the server and build items from the 
	 * data received 
	 */
	public async fetchAndBuild(): Promise<void> {
		// TODO implement filtering

		Spinner.showSpinner("Fetching Software Data...", this.containerElement);

		this.itemData = [...await ModelDataCache.getModelDataAll("VisibleSoftware")];
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