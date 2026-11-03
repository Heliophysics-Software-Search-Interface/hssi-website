import {
	OrcidFinder, PopupDialogue, RorFinder, DoiDataciteFinder, 
	UrlWidget, faMagicIcon, propResultFilters,
	type JSONObject,
	type OrcidItem,
	ModelMultiSubfield
} from "../../loader"

/** `"button-find"`: CSS class for the find button. */
export const findButtonStyle = "button-find";
/**
 * `"emphasis-anim"`: CSS class that animates the find button to draw attention
 * to it.
 */
export const styleEmphasisAnimation = "emphasis-anim";

/**
 * Base class for URL inputs with a "find" button that opens an identifier
 * search popup.
 */
export abstract class FindIdWidget extends UrlWidget {

	private emphasized: boolean = false;
	/** The find button. */
	protected findButton: HTMLButtonElement = null;
	/** Find button label; `"find"`. */
	protected get findButtonText(): string { return "find"; }
	/** Example identifier shown in the input placeholder; empty by default. */
	protected get placeholderExample(): string { return ""; }

	/** Called when the find button is clicked; opens the search popup. */
	protected abstract onFindButtonPressed(): void;
	/**
	 * Called with the selected result's data when the user picks one in the
	 * search popup; does nothing by default.
	 */
	public onDataSelected(data: JSONObject): void { }

	/**
	 * Builds the find button beside the input; it animates the first time the
	 * empty input is focused.
	 */
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

	/**
	 * Also builds the find button (unless read-only) and sets the placeholder.
	 * Overrides `Widget.initialize`.
	 */
	override initialize(readOnly: boolean = false): void {
		super.initialize(readOnly);
		if(!readOnly) this.buildFindButton();
		this.inputElement.placeholder = "Use 'find' button or paste URL ";
		if(this.placeholderExample) {
			this.inputElement.placeholder += "(ex: " + this.placeholderExample + ")";
		}
	}
}

/** Input for a ROR organization identifier. */
export class RorWidget extends FindIdWidget {
	/**
	 * `"https://ror.org/00000xxxx"`. Overrides
	 * `FindIdWidget.placeholderExample`.
	 */
	protected get placeholderExample(): string { 
		return "https://ror.org/00000xxxx";
	}
	/**
	 * Opens the `RorFinder` popup for this field. Overrides
	 * `FindIdWidget.onFindButtonPressed`.
	 */
	protected override onFindButtonPressed(): void {
		const rorPopup = RorFinder.getInstance()
			.setTarget(this.parentField)
			.withFilters(this.properties[propResultFilters]);
		PopupDialogue.showPopup(rorPopup);
	}
}

/** Input for an ORCID person identifier. */
export class OrcidWidget extends FindIdWidget {
	/**
	 * `"https://orcid.org/0000-0000-0000-0000"`. Overrides
	 * `FindIdWidget.placeholderExample`.
	 */
	protected get placeholderExample(): string { 
		return "https://orcid.org/0000-0000-0000-0000"; 
	}
	/**
	 * Opens the `OrcidFinder` popup for this field. Overrides
	 * `FindIdWidget.onFindButtonPressed`.
	 */
	protected override onFindButtonPressed(): void {
		const orcidPopup = OrcidFinder.getInstance()
			.setTarget(this.parentField)
			.withFilters(this.properties[propResultFilters]);
		PopupDialogue.showPopup(orcidPopup);
	}

	/**
	 * Fills the last sibling multi-field (assumed to be affiliations) with the
	 * ORCID record's institutions, unless it already has valid input. Overrides
	 * `FindIdWidget.onDataSelected`.
	 */
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

/** Input for a DataCite DOI. */
export class DataciteDoiWidget extends FindIdWidget {
	/**
	 * `"https://doi.org/10.5281/zenodo.00000000"`. Overrides
	 * `FindIdWidget.placeholderExample`.
	 */
	protected get placeholderExample(): string {
		return "https://doi.org/10.5281/zenodo.00000000";
	}
	/**
	 * Opens the `DoiDataciteFinder` popup for this field. Overrides
	 * `FindIdWidget.onFindButtonPressed`.
	 */
	protected override onFindButtonPressed(): void {
		const popup = DoiDataciteFinder.getInstance()
			.setTarget(this.parentField)
			.withFilters(this.properties[propResultFilters]);
		PopupDialogue.showPopup(popup);
	}
}

/**
 * Author identifier input with an "Is Organization" checkbox that switches
 * between ORCID and ROR mode.
 */
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

	/**
	 * ROR example in organization mode, ORCID example otherwise. Overrides
	 * `FindIdWidget.placeholderExample`.
	 */
	protected override get placeholderExample(): string {
		return this.isOrgMode
			? "https://ror.org/00000xxxx"
			: "https://orcid.org/0000-0000-0000-0000";
	}

	/**
	 * Opens the `RorFinder` popup in organization mode, otherwise the
	 * `OrcidFinder` popup. Overrides `FindIdWidget.onFindButtonPressed`.
	 */
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

	/**
	 * In ORCID mode, fills the last sibling multi-field (assumed to be
	 * affiliations) with the record's institutions unless it already has valid
	 * input. Overrides `FindIdWidget.onDataSelected`.
	 */
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
			const valueForRor = this.isOrcidUrl(currentValue) ? "" : currentValue;
			this.switchToRorMode(valueForRor);
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

	/**
	 * Also switches to ROR or ORCID mode to match a ROR or ORCID URL. Overrides
	 * `Widget.setValue`.
	 */
	override setValue(value: string, notify: boolean = true): void {
		super.setValue(value, notify);
		if (!this.isOrgCheckbox) return;
		if (this.isRorUrl(value)) this.switchToRorMode(value);
		else if (this.isOrcidUrl(value)) this.switchToOrcidMode();
	}

	/**
	 * Also builds the checkbox and switches mode as the user types a ROR or
	 * ORCID URL; in organization mode, non-ROR values are marked invalid.
	 * Overrides `Widget.initialize`.
	 */
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