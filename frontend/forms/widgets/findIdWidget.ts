import {
	OrcidFinder, PopupDialogue, RorFinder, DoiDataciteFinder, 
	UrlWidget, faMagicIcon, propResultFilters,
	type JSONObject,
	type OrcidItem,
	ModelMultiSubfield
} from "../../loader"

export const findButtonStyle = "button-find";
export const styleEmphasisAnimation = "emphasis-anim";

export abstract class FindIdWidget extends UrlWidget {

	private emphasized: boolean = false;
	protected findButton: HTMLButtonElement = null;
	protected get findButtonText(): string { return "find"; }
	protected get placeholderExample(): string { return ""; }

	protected abstract onFindButtonPressed(): void;
	public onDataSelected(data: JSONObject): void { }

	protected buildFindButton(): void {
		
		let rowContainer = document.createElement("div");
		rowContainer.style.display = "flex";
		rowContainer.style.verticalAlign = "center";

		this.findButton = document.createElement("button");
		this.findButton.type = "button";
		this.findButton.classList.add(findButtonStyle);
		this.findButton.innerHTML = faMagicIcon + " " + this.findButtonText;
		this.findButton.addEventListener("click", () => {
			this.onFindButtonPressed();
			this.emphasized = true;
		});
		this.findButton.title = "popup dialogue to search for your identifier";

		this.inputElement.style.flex = "1";
		rowContainer.appendChild(this.findButton);
		rowContainer.appendChild(this.inputElement);

		this.element.appendChild(rowContainer);

		// add emphasis animation
		const inElem = this.getInputElement();
		inElem.addEventListener("focusin", e => {
			if(!this.emphasized && !this.parentField?.hasValidInput()) {
				this.findButton.classList.add(styleEmphasisAnimation);
				this.emphasized = true;
			}
		}, {once: true});
	}

	override initialize(readOnly: boolean = false): void {
		super.initialize(readOnly);
		if(!readOnly) this.buildFindButton();
		this.inputElement.placeholder = "Use 'find' button or paste URL ";
		if(this.placeholderExample) {
			this.inputElement.placeholder += "(ex: " + this.placeholderExample + ")";
		}
	}
}

export class RorWidget extends FindIdWidget {
	protected get placeholderExample(): string { 
		return "https://ror.org/00000xxxx";
	}
	protected override onFindButtonPressed(): void {
		const rorPopup = RorFinder.getInstance()
			.setTarget(this.parentField)
			.withFilters(this.properties[propResultFilters]);
		PopupDialogue.showPopup(rorPopup);
	}
}

export class OrcidWidget extends FindIdWidget {
	protected get placeholderExample(): string { 
		return "https://orcid.org/0000-0000-0000-0000"; 
	}
	protected override onFindButtonPressed(): void {
		const orcidPopup = OrcidFinder.getInstance()
			.setTarget(this.parentField)
			.withFilters(this.properties[propResultFilters]);
		PopupDialogue.showPopup(orcidPopup);
	}

	override onDataSelected(data: JSONObject): void {
		super.onDataSelected(data);

		// we need to find a field that could be the affiliation field of the 
		// author, since we don't know exactly the sibling field structure, 
		// we will have to assume that the first multifield found is the 
		// affiliation field
		const field = this.parentField;
		const siblings = field.parent?.getSubfields() ?? [];
		let affiliationField: ModelMultiSubfield = null;
		for(const sibling of siblings){
			if(sibling instanceof ModelMultiSubfield){
				affiliationField = sibling;
			}
		}
		
		// don't do anything if there's no affiliation, or if affiliations are 
		// already filled out by the user
		if(!affiliationField || affiliationField.hasValidInput()) return;
		
		// fill the affiliations given the data from orcid
		const orcidData = data as OrcidItem
		const affiliationNames = orcidData["institution-name"];
		affiliationField.clearField();
		for(const affilName of affiliationNames){
			const field = affiliationField.addNewMultifieldWithValue(affilName);
			field.expandSubfields();
		}
	}
}

export class DataciteDoiWidget extends FindIdWidget {
	protected get placeholderExample(): string { 
		return "https://doi.org/10.5281/zenodo.00000000";
	}
	protected override onFindButtonPressed(): void {
		const popup = DoiDataciteFinder.getInstance()
			.setTarget(this.parentField)
			.withFilters(this.properties[propResultFilters]);
		PopupDialogue.showPopup(popup);
	}
}