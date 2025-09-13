import { 
	appendPromisedElement,
	ModelChipBuilder,
	type SoftwareData,
} from "../loader";

const styleResourceItem = "resource-item";
const styleResourceHeader = "resource-header";
const styleResourceTitle = "resource-title";
const styleDescription = "description";
const styleExpandButton = "expand-button";
const styleBottomButtons = "bottom-buttons";
const styleAuthor = "author";
const styleLinkBtn = "link-btn";
const styleBtnCode = "btn-code";
const styleBtnDocs = "btn-docs";
const styleBtnPublication = "btn-publication";
const styleBtnDoi = "btn-doi";
const styleHeaderChips = "header-chips";

const faBook = `<i class="fa fa-book"></i>`;
const faLink = `<i class="fa fa-link"></i>`;
const faCode = `<i class="fa fa-code"></i>`;
const faNews = `<i class="fa fa-news"></i>`;
const faFile = `<i class="fa fa-file"></i>`;
const faDownArrow = `<i class="fa fa-angle-down"></i>`
const faUpArrow = `<i class="fa fa-angle-up"></i>`

/**
 * represents a single software resource submitted to the HSSI database, 
 * rendered to html for the user to interactwith
 */
export class ResourceItem{

	private data: SoftwareData = null;
	private shrinkedContent: HTMLDivElement = null;
	private expandedContent: HTMLDivElement = null;
	private expandButton: HTMLButtonElement = null;
	private headerDiv: HTMLDivElement = null;

	/** the html element that contains all the html content for this item */
	public containerElement: HTMLDivElement = null;

	public constructor(){
		this.containerElement = document.createElement("div");
		this.containerElement.classList.add(styleResourceItem);
		this.containerElement.style.position = "relative";
	}

	private buildLinkButtons(): void {
		const bottomButtonContainer = document.createElement("div");
		bottomButtonContainer.classList.add(styleBottomButtons);
		this.containerElement.appendChild(bottomButtonContainer);
		
		if(this.data.codeRepositoryUrl){
			const repoButton = document.createElement("a");
			repoButton.classList.add(styleLinkBtn);
			repoButton.classList.add(styleBtnCode);
			repoButton.innerHTML = faCode + " Code";
			repoButton.href = this.data.codeRepositoryUrl;
			bottomButtonContainer.appendChild(repoButton);
		}

		if(this.data.documentation){
			const docsButton = document.createElement("a");
			docsButton.classList.add(styleLinkBtn);
			docsButton.classList.add(styleBtnDocs);
			docsButton.innerHTML = faBook + " Docs";
			docsButton.href = this.data.documentation;
			bottomButtonContainer.appendChild(docsButton);
		}

		if(this.data.referencePublication){
			const refpubButton = document.createElement("a");
			refpubButton.classList.add(styleLinkBtn);
			refpubButton.classList.add(styleBtnPublication);
			refpubButton.innerHTML = faFile + " Publication";
			refpubButton.href = this.data.referencePublication.identifier;
			bottomButtonContainer.appendChild(refpubButton);
		}

		if(this.data.persistentIdentifier){
			const doiButton = document.createElement("a");
			doiButton.classList.add(styleLinkBtn);
			doiButton.classList.add(styleBtnDoi);
			doiButton.innerHTML = faLink + "DOI";
			doiButton.href = this.data.persistentIdentifier;
			bottomButtonContainer.appendChild(doiButton);
		}
	}

	private buildModelChips(): void {
		const chipContainer = document.createElement("div");
		chipContainer.classList.add(styleHeaderChips);
		this.headerDiv.appendChild(chipContainer);
		
		const categoryChips = document.createElement("div");
		chipContainer.appendChild(categoryChips);

		// add each unique top-level category to the container
		const categoriesAdded = new Set<string>();
		for(const category of this.data.softwareFunctionality) {
			
			// get id or parent id if its a child, mark id as added
			const targetId = category.parents?.at(0) ?? category.id;
			if(categoriesAdded.has(targetId)) continue;
			categoriesAdded.add(targetId);

			// create visual ui element and add to resource
			appendPromisedElement(
				categoryChips, 
				ModelChipBuilder.createChip("FunctionCategory",targetId)
			);
		}
		
		const proglangChips = document.createElement("div")
		chipContainer.appendChild(proglangChips);
		
		// no need to check for uniqueness because db table already does
		for(const lang of this.data.programmingLanguage) {
			appendPromisedElement(
				proglangChips, 
				ModelChipBuilder.createChip("ProgrammingLanguage", lang.id)
			);
		}
	}

	private build(): void {
		// TODO build from this.data
		this.headerDiv = document.createElement("div");
		this.headerDiv.classList.add(styleResourceHeader);
		this.containerElement.appendChild(this.headerDiv);

		const headerText = document.createElement("div");
		this.headerDiv.appendChild(headerText);
		
		const titleDiv = document.createElement("div");
		titleDiv.classList.add(styleResourceTitle);
		titleDiv.innerText = this.data.softwareName;
		headerText.appendChild(titleDiv);

		const headInfoDiv = document.createElement("div");
		headerText.appendChild(headInfoDiv);

		const authors = document.createElement("span");
		headInfoDiv.appendChild(authors)

		for(let i = 0; i < this.data.authors.length; i++){
			const author = this.data.authors[i];
			const authSpan = document.createElement("span");
			authSpan.classList.add(styleAuthor);
			authSpan.innerText = author.firstName || "";
			if (author.firstName) authSpan.innerText += " ";
			authSpan.innerText += author.lastName;
			if(author.identifier){
				const authAnchor = document.createElement("a");
				authAnchor.href = author.identifier;
				authAnchor.appendChild(authSpan);
				headInfoDiv.appendChild(authAnchor);
			}
			else headInfoDiv.appendChild(authSpan);
			if(i < this.data.authors.length - 1) headInfoDiv.innerHTML += "; ";
		}

		this.shrinkedContent = document.createElement("div");
		this.containerElement.appendChild(this.shrinkedContent);
		
		const conciseDescDiv = document.createElement("div");
		conciseDescDiv.classList.add(styleDescription);
		conciseDescDiv.innerText = this.data.conciseDescription;
		this.shrinkedContent.appendChild(conciseDescDiv);
		
		this.expandedContent = document.createElement("div");
		this.containerElement.appendChild(this.expandedContent);
		
		const descriptionDiv = document.createElement("div");
		descriptionDiv.classList.add(styleDescription);
		descriptionDiv.innerText = this.data.description;
		this.expandedContent.appendChild(descriptionDiv);
		
		// TODO add logo

		this.buildLinkButtons();
		this.buildModelChips();

		// Expand button:
		this.expandButton = document.createElement("button");
		this.expandButton.classList.add(styleExpandButton);
		this.expandButton.innerHTML = faDownArrow;

		this.expandButton.addEventListener("click", e => 
			this.setExpanded(!this.isExpanded())
		);

		this.containerElement.appendChild(this.expandButton);
		this.setExpanded(false);
	}

	public setExpanded(expand: boolean): void {
		if(expand){
			this.expandedContent.style.display = "block";
			this.shrinkedContent.style.display = "none";
			this.expandButton.innerHTML = faUpArrow;
		} 
		else {
			this.expandedContent.style.display = "none";
			this.shrinkedContent.style.display = "block";
			this.expandButton.innerHTML = faDownArrow;
		}
	}

	/** returns true if the hidden expandedcontent div is visible */
	public isExpanded(): boolean {
		return this.expandedContent.style.display !== "none";
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