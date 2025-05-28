/** */

export const requirementAttribute = "data-hssi-required";
export const requirementAttributeContainer = "data-hssi-required-container";

export const invalidRecStyle = "invalid-recommended";
export const invalidManStyle = "invalid-mandatory";
export const noteStyle = "note"

export enum RequirementLevel {
	/** its optional - unnecessary if not relevant */
	OPTIONAL = 0,
	/** its recommended to not be left blank */
	RECOMMENDED = 1,
	/** it must be filled or else the form cannot be submitted */
	MANDATORY = 2,
}

const acceptableInputElementQueries = [
	"input",
	"textarea",
	"select",
];

interface FormElement extends HTMLElement {
	required: boolean;
	type: string;
	value: string;
	checkValidity: () => boolean;
}

export class FieldRequirement {

	public element: FormElement = null;
	public elementContainer: HTMLElement = null;
	public noteElement: HTMLDivElement = null;
	public requirementLevel: RequirementLevel = RequirementLevel.OPTIONAL;
	
	public constructor(
		element: FormElement, 
		requirementLevel: RequirementLevel, 
		container: HTMLElement = null
	) {
		this.elementContainer = container
		this.element = element;
		this.requirementLevel = requirementLevel;
		this.createNoteElement();
	}

	/// Private methods --------------------------------------------------------

	private isValidNonNull(): boolean {
		if(this.element instanceof HTMLInputElement) {
			switch(this.element.type) {
				case "text": case "email": case "url": case "tel": case "search": 
				case "number": case "date": case "datetime-local": case "month": 
				case "week": case "time": case "color": case "range": 
					return this.element.checkValidity() && this.element.value.trim().length > 0;
				case "checkbox": case "radio":
					return this.element.checkValidity() && (this.element as any).checked;
			}
		}
		else if (this.element instanceof HTMLTextAreaElement) {
			return this.element.checkValidity() && this.element.value.trim().length > 0;
		}
		return true;
	}

	private createNoteElement(): void {
		this.noteElement = document.createElement("div");
		this.noteElement.classList.add(noteStyle);
		this.noteElement.style.display = "none";
		this.getStyledElement().insertAdjacentElement("afterend", this.noteElement);
	}

	private getNoteText(): string {
		const valid = this.isValidNonNull();
		if(valid || this.requirementLevel == RequirementLevel.OPTIONAL) return "";

		let note = "";
		switch(this.requirementLevel){
			case RequirementLevel.MANDATORY: 
				note = "This field is mandatory";
				break;
			case RequirementLevel.RECOMMENDED: 
				note = "This field is recommended";
				break;
		}
		return note;
	}

	/// Public methods ---------------------------------------------------------

	/** returns the element that the invalid-* class style is applied to */
	public getStyledElement(): HTMLElement {
		return this.elementContainer ?? this.element;
	}

	public applyValidityStyle(): void{
		this.onFocusEnter(null);
		this.onFocusExit(null);
	}

	/// Event listeners --------------------------------------------------------

	private onFocusEnter(_e: FocusEvent): void {
		// remove invalid style
		let className = "";
		switch(this.requirementLevel) {
			case RequirementLevel.RECOMMENDED: className = invalidRecStyle; break;
			case RequirementLevel.MANDATORY: className = invalidManStyle; break;
		}
		this.getStyledElement().classList.remove(className);
		this.noteElement.classList.remove(className);
		this.noteElement.style.display = "none";
	}

	private onFocusExit(_e: FocusEvent): void {

		// no need to add invalid styles if it is filled out
		if(this.isValidNonNull()) return;

		// add invalid style
		let className = "";
		switch(this.requirementLevel) {
			case RequirementLevel.OPTIONAL: return;
			case RequirementLevel.RECOMMENDED: className = invalidRecStyle; break;
			case RequirementLevel.MANDATORY: className = invalidManStyle; break;
		}

		// add class to required element/container if applicable
		this.getStyledElement().classList.add(className);
		this.noteElement.classList.add(className);
		this.noteElement.style.display = "block";
		this.noteElement.innerText = this.getNoteText();
	}

	/// Static properties ------------------------------------------------------

	/** 
	 * contains all required widgets in a given form with a requirement level 
	 * greater than OPTIONAL
	*/
	private static all: FieldRequirement[] = [];

	/** map applicable elements to their corresponding required input object */
	private static elementMap: Map<HTMLElement, FieldRequirement> = new Map();

	/// Static methods ---------------------------------------------------------

	/** finds all required widgets in the document and stores them */
	private static findRequiredInputs(): void {
		this.all.length = 0;

		// query for individual inpputs with specified requirement levels
		const elements = document.querySelectorAll(`[${requirementAttribute}]`);
		for(const elem of elements) {

			// must be a form element
			if(!(elem instanceof HTMLInputElement)) 
				if (!(elem instanceof HTMLTextAreaElement)) 
					if (!(elem instanceof HTMLSelectElement))
						continue;

			// we don't want to double count inputs that are children of containers
			const container = elem.closest(`[${requirementAttributeContainer}]`);
			if(container != null) {
				elem.removeAttribute(requirementAttribute);
				continue;
			}

			const elemReqLvl = Number.parseInt(elem.getAttribute(requirementAttribute));
			if(elemReqLvl > RequirementLevel.OPTIONAL) {
				const reqIn = new FieldRequirement(elem as FormElement, elemReqLvl);
				this.all.push(reqIn);
				this.elementMap.set(elem, reqIn);
			}
		}

		// query for all containers (for widgets with potential multi input elements)
		const containers = document.querySelectorAll(`[${requirementAttributeContainer}]`);
		for(const container of containers) {
			if(!(container instanceof HTMLElement)) continue;

			// find an acceptable element to consider the field input element
			let elem: HTMLElement = null;
			for(const query of acceptableInputElementQueries){
				if(elem) break;
				elem = container.querySelector(query);
			}

			// error if no acceptable input element was found
			if(!elem) {
				console.log(container);
				throw new Error("No input found in container with requirement attribute");
			}

			// create the field requirement object and register it
			const elemReqLvl = Number.parseInt(
				container.getAttribute(requirementAttributeContainer)
			);
			const reqIn = new FieldRequirement(
				elem as FormElement, 
				elemReqLvl, 
				container as HTMLElement
			)
			this.all.push(reqIn);
			this.elementMap.set(container, reqIn);
		}
	}

	public static applyRequirementLevels(): void {

		// iterate through all inputs
		this.findRequiredInputs();
		console.log("found " + this.all.length + " required inputs");
		for(const input of this.all) {

			// enforce required attribute if mandatory
			if(input.requirementLevel == RequirementLevel.MANDATORY) {
				input.element.required = true;
			}

			// remove required attribute if it is not mandatory
			else {
				input.element.required = false;
			}

			// add focus event listeners
			if(input.requirementLevel > RequirementLevel.OPTIONAL) {
				input.element.addEventListener("focusin", (e) => {
					input.onFocusEnter(e);
				});
				input.element.addEventListener("focusout", (e) => {
					input.onFocusExit(e);
				});
			}
		}
	}

	/** 
	 * get the associated {@link FieldRequirement} object from a given html element
	 */
	public static getFromElement(element: HTMLElement): FieldRequirement {
		if(this.elementMap.has(element)) {
			return this.elementMap.get(element);
		}
		return null;
	}
}