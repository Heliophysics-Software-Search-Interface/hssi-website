import { 
	apiModel, apiSlugRowsAll, fetchTimeout, modelApiUrl, ModelData, ResourceItem, 
	Spinner, 
	type JSONArray, type JSONObject, type SoftwareData,
} from "../loader";

const styleNoResults = "no-results";

const softwarModelName = "VisibleSoftware";

/** 
 * a list-style display that shows users different software resource entries 
 * from within the HSSI database
 */
export class ResourceView {

	private itemData: JSONArray<JSONObject> = [];
	private items: ResourceItem[] = [];
	
	/** element to display when no results */
	private get noResultsElement(): HTMLElement {
		return document.body.getElementsByClassName(styleNoResults)[0] as any;
	}

	/** the html element that contains all the html content for this view */
	public containerElement: HTMLDivElement = null;

	public constructor() {
		this.containerElement = document.createElement("div");
		this.containerElement.style.minHeight = "100px";
	}

	/** create new items based on stored item data */
	private refreshItems(): void {

		// remove all old items
		for(const oldItem of this.items) oldItem.destroy();
		this.items.length = 0;

		// create new items from data
		for(const data of this.itemData) {
			const item = ResourceItem.createFromData(data as SoftwareData);
			this.containerElement.appendChild(item.containerElement);
			this.items.push(item);
		}

		// display no results if no results found, or hide it if there is results
		const noResultsElem = this.noResultsElement;
		console.log(noResultsElem)
		if(noResultsElem){
			if(this.items.length <= 0) this.noResultsElement.style.display = "block";
			else this.noResultsElement.style.display = "none";
		}
	}

	/** fetches resources from the server and store their data */
	private async fetchResourceItems(): Promise<void> {
		// TODO implement querying

		// fetch all software objects from the database
		this.itemData = await ModelData.getModelData(softwarModelName);
	}

	/** 
	 * fetch item data from the server and build items from the 
	 * data received 
	 */
	public async fetchAndBuild(): Promise<void> {
		// TODO implement querying

		Spinner.showSpinner("Fetching Software Data...", this.containerElement);

		await this.fetchResourceItems();
		this.refreshItems();

		Spinner.hideSpinner(this.containerElement);
	}
}

function makeResourceView() {
	const view = new ResourceView();
	document.currentScript.parentNode.appendChild(view.containerElement);
	view.fetchAndBuild();
}

// expose to global
const win = window as any;
win.makeResourceView = makeResourceView;