import { 
	apiModel, apiSlugRowsAll, fetchTimeout, ResourceItem, 
	type JSONArray, type JSONObject, type SoftwareData,
} from "../loader";

const softwarModelName = "VisibleSoftware";

/** 
 * a list-style display that shows users different software resource entries 
 * from within the HSSI database
 */
export class ResourceView {

	private itemData: JSONArray<JSONObject> = [];
	private items: ResourceItem[] = [];

	/** the html element that contains all the html content for this view */
	public containerElement: HTMLDivElement = null;

	public constructor() {
		this.containerElement = document.createElement("div");
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
	}

	/** fetches resources from the server and store their data */
	private async fetchResourceItems(): Promise<void> {
		// TODO implement querying

		// fetch all software objects from the database
		const url = apiModel + softwarModelName + apiSlugRowsAll + "?recursive=true";
		const result = await fetchTimeout(url);
		const data = await result.json();
		console.log(data);
		this.itemData = data.data;
	}

	/** 
	 * fetch item data from the server and build items from the 
	 * data received 
	 */
	public async fetchAndBuild(): Promise<void> {
		// TODO implement querying

		await this.fetchResourceItems();
		this.refreshItems();
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