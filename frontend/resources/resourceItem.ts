import { 
	type JSONObject, type SoftwareData,
} from "../loader";

const styleResourceItem = "resource-item";
const styleResourceHeader = "resource-header";
const styleResourceTitle = "resource-title";
const styleDescription = "description";

/**
 * represents a single software resource submitted to the HSSI database, 
 * rendered to html for the user to interactwith
 */
export class ResourceItem{

	private data: SoftwareData = null;

	/** the html element that contains all the html content for this item */
	public containerElement: HTMLDivElement = null;

	public constructor(){
		this.containerElement = document.createElement("div");
		this.containerElement.classList.add(styleResourceItem);
	}

	private build(): void {
		// TODO build from this.data
		const headerDiv = document.createElement("div");
		headerDiv.classList.add(styleResourceHeader);
		this.containerElement.appendChild(headerDiv);
		
		const titleDiv = document.createElement("div");
		titleDiv.classList.add(styleResourceTitle);
		titleDiv.innerText = this.data.softwareName;
		headerDiv.appendChild(titleDiv);

		const headInfoDiv = document.createElement("div");
		headInfoDiv.innerText = "Lorem Ipsum";
		headerDiv.appendChild(headInfoDiv);

		const descContainerDiv = document.createElement("div");
		this.containerElement.appendChild(descContainerDiv);

		const descriptionDiv = document.createElement("div");
		descriptionDiv.classList.add(styleDescription);
		descriptionDiv.innerText = this.data.description;
		descContainerDiv.appendChild(descriptionDiv);

		const conciseDescDiv = document.createElement("div");
		conciseDescDiv.classList.add(styleDescription);
		conciseDescDiv.innerText = this.data.conciseDescription;
		descContainerDiv.appendChild(conciseDescDiv);

		// TODO add logo

		// TODO add buttons: repo, docs, doi, ref pub, 
	}

	/** destroy and remove item from DOM */
	public destroy(): void {
		// TODO 
	}

	/**
	 * create a new software entry resource ready for display, given json data
	 * pulled from the database Software table
	 * @param data the json data to base the item off of
	 */
	public static createFromData(data: SoftwareData): ResourceItem {
		const r = new ResourceItem();
		r.data = data;
		r.build();
		return r;
	}
}