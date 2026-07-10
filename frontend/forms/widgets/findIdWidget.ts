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

export class AuthorIdentifierWidget extends FindIdWidget {

	private isOrgCheckbox: HTMLInputElement = null;
	private isOrgMode: boolean = false;

	private static readonly ROR_PREFIX = "https://ror.org/";
	private static readonly ROR_PATTERN = /^https?:\/\/ror\.org\//;
	private static readonly ORCID_PATTERN = /^https?:\/\/orcid\.org\//;

	private isRorUrl(url: string): boolean {
		return AuthorIdentifierWidget.ROR_PATTERN.test(url);
	}

	private isOrcidUrl(url: string): boolean {
		return AuthorIdentifierWidget.ORCID_PATTERN.test(url);
	}

	protected override get placeholderExample(): string {
		return this.isOrgMode
			? "https://ror.org/00000xxxx"
			: "https://orcid.org/0000-0000-0000-0000";
	}

	protected override onFindButtonPressed(): void {
		if (this.isOrgMode) {
			const rorPopup = RorFinder.getInstance()
				.setTarget(this.parentField)
				.withFilters(this.properties[propResultFilters]);
			PopupDialogue.showPopup(rorPopup);
		} else {
			const orcidPopup = OrcidFinder.getInstance()
				.setTarget(this.parentField)
				.withFilters(this.properties[propResultFilters]);
			PopupDialogue.showPopup(orcidPopup);
		}
	}

	override onDataSelected(data: JSONObject): void {
		super.onDataSelected(data);
		if (this.isOrgMode) return;

		const field = this.parentField;
		const siblings = field.parent?.getSubfields() ?? [];
		let affiliationField: ModelMultiSubfield = null;
		for (const sibling of siblings) {
			if (sibling instanceof ModelMultiSubfield) affiliationField = sibling;
		}
		if (!affiliationField || affiliationField.hasValidInput()) return;

		const orcidData = data as OrcidItem;
		const affiliationNames = orcidData["institution-name"];
		affiliationField.clearField();
		for (const affilName of affiliationNames) {
			const f = affiliationField.addNewMultifieldWithValue(affilName);
			f.expandSubfields();
		}
	}

	private buildCheckbox(readOnly: boolean): void {
		const label = document.createElement("label");
		label.style.display = "flex";
		label.style.alignItems = "center";
		label.style.gap = "0.35em";
		label.style.fontSize = "0.85em";
		label.style.marginBottom = "0.25em";
		label.style.userSelect = "none";
		label.style.cursor = "pointer";

		this.isOrgCheckbox = document.createElement("input");
		this.isOrgCheckbox.type = "checkbox";
		this.isOrgCheckbox.disabled = readOnly;

		label.appendChild(this.isOrgCheckbox);
		label.appendChild(document.createTextNode("Is Organization"));
		this.element.appendChild(label);

		if (!readOnly) {
			this.isOrgCheckbox.addEventListener("change", () => this.onCheckboxChange());
		}
	}

	private onCheckboxChange(): void {
		const currentValue = this.inputElement?.value ?? "";
		if (this.isOrgCheckbox.checked) {
			if (this.isOrcidUrl(currentValue)) {
				this.isOrgCheckbox.checked = false;
				return;
			}
			this.switchToRorMode(currentValue);
		} else {
			this.switchToOrcidMode();
		}
	}

	private switchToRorMode(currentValue: string): void {
		this.isOrgMode = true;
		this.isOrgCheckbox.checked = true;
		if (!currentValue) this.inputElement.value = AuthorIdentifierWidget.ROR_PREFIX;
		this.inputElement.placeholder =
			"Use 'find' button or paste URL (ex: " + this.placeholderExample + ")";
		this.updateValidationState();
	}

	private switchToOrcidMode(): void {
		this.isOrgMode = false;
		this.isOrgCheckbox.checked = false;
		const currentValue = this.inputElement?.value ?? "";
		if (this.isRorUrl(currentValue)) this.inputElement.value = "";
		this.inputElement.placeholder =
			"Use 'find' button or paste URL (ex: " + this.placeholderExample + ")";
		this.updateValidationState();
	}

	private updateValidationState(): void {
		const value = this.inputElement?.value ?? "";
		if (this.isOrgMode && value && !this.isRorUrl(value)) {
			this.inputElement.setCustomValidity(
				"Organization identifier must be a ROR URL (https://ror.org/...)"
			);
		} else {
			this.inputElement.setCustomValidity("");
		}
	}

	override setValue(value: string, notify: boolean = true): void {
		super.setValue(value, notify);
		if (!this.isOrgCheckbox) return;
		if (this.isRorUrl(value)) this.switchToRorMode(value);
		else if (this.isOrcidUrl(value)) this.switchToOrcidMode();
	}

	override initialize(readOnly: boolean = false): void {
		this.buildCheckbox(readOnly);
		super.initialize(readOnly);
		this.inputElement.addEventListener("input", () => {
			this.updateValidationState();
			const val = this.inputElement.value;
			if (this.isRorUrl(val) && !this.isOrgMode) this.switchToRorMode(val);
			else if (this.isOrcidUrl(val) && this.isOrgMode) this.switchToOrcidMode();
		});
	}
}