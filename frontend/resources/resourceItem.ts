import { 
	type JSONObject, type SoftwareData,
} from "../loader";

const styleResourceItem = "resource-item";
const styleResourceHeader = "resource-header";
const styleResourceTitle = "resource-title";
const styleDescription = "description";
const styleBottomButtons = "bottom-buttons";

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
		headerDiv.appendChild(headInfoDiv);

		const authors = document.createElement("span");
		headInfoDiv.appendChild(authors)

		for(let i = 0; i < this.data.authors.length; i++){
			const author = this.data.authors[i];
			const authSpan = document.createElement("span");
			authSpan.innerText = author.firstName || "";
			if (author.firstName) authSpan.innerText += " ";
			authSpan.innerText += author.lastName;
			if(i < this.data.authors.length - 1) authSpan.innerText += "; ";
			headInfoDiv.appendChild(authSpan);
		}

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

		const bottomButtonContainer = document.createElement("div");
		bottomButtonContainer.classList.add(styleBottomButtons);
		this.containerElement.appendChild(bottomButtonContainer);
		
		if(this.data.codeRepositoryUrl){
			const repoButton = document.createElement("a");
			repoButton.innerText = "Code";
			repoButton.href = this.data.codeRepositoryUrl;
			bottomButtonContainer.appendChild(repoButton);
		}

		if(this.data.documentation){
			const docsButton = document.createElement("a");
			docsButton.innerText = "Documentation";
			docsButton.href = this.data.documentation;
			bottomButtonContainer.appendChild(docsButton);
		}

		if(this.data.referencePublication){
			const refpubButton = document.createElement("a");
			refpubButton.innerText = "Publication";
			refpubButton.href = this.data.referencePublication.identifier;
			bottomButtonContainer.appendChild(refpubButton);
		}

		if(this.data.persistentIdentifier){
			const doiButton = document.createElement("a");
			doiButton.innerText = "DOI";
			doiButton.href = this.data.persistentIdentifier;
			bottomButtonContainer.appendChild(doiButton);
		}
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