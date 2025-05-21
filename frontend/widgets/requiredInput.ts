/** */

import { Widget } from "../loader";

export const requirementAttribute = "data-hssi-required";

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

interface FormElement extends HTMLElement {
	required: boolean;
	checkValidity: () => boolean;
}

export class RequiredInput {

	public element: FormElement = null;
	public noteElement: HTMLDivElement = null;
	public requirementLevel: RequirementLevel = RequirementLevel.OPTIONAL;
	
	public constructor(element: FormElement, requirementLevel: RequirementLevel) {
		this.element = element;
		this.requirementLevel = requirementLevel;
		this.createNoteElement();
	}

	private createNoteElement(): void {
		this.noteElement = document.createElement("div");
		this.noteElement.classList.add(noteStyle);
		this.noteElement.style.display = "none";
		this.element.insertAdjacentElement("afterend", this.noteElement);
	}

	private getNoteText(): string {
		const valid = this.element.checkValidity();
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

	private onFocusEnter(e: FocusEvent): void {
		// remove invalid style
		let className = "";
		switch(this.requirementLevel) {
			case RequirementLevel.RECOMMENDED: className = invalidRecStyle; break;
			case RequirementLevel.MANDATORY: className = invalidManStyle; break;
		}
		this.element.classList.remove(className);
		this.noteElement.classList.remove(className);
		this.noteElement.style.display = "none";
	}

	private onFocusExit(e: FocusEvent): void {
		
		// no need to add invalid styles if it is filled out
		if(this.element.checkValidity()) return;

		// add invalid style
		let className = "";
		switch(this.requirementLevel) {
			case RequirementLevel.RECOMMENDED: className = invalidRecStyle; break;
			case RequirementLevel.MANDATORY: className = invalidManStyle; break;
		}
		this.element.classList.add(className);
		this.noteElement.classList.add(className);
		this.noteElement.style.display = "block";
		this.noteElement.innerText = this.getNoteText();
	}

	/** 
	 * contains all required widgets in a given form with a requirement level 
	 * greater than OPTIONAL
	*/
	private static all: RequiredInput[] = [];

	/** finds all required widgets in the document and stores them */
	private static findRequiredInputs(): void {
		this.all.length = 0;
		const elements = document.querySelectorAll(`input[${requirementAttribute}]`);
		for(const elem of elements) {
			const elemReqLvl = Number.parseInt(elem.getAttribute(requirementAttribute));
			if(elemReqLvl > RequirementLevel.OPTIONAL) {
				this.all.push(new RequiredInput(elem as FormElement, elemReqLvl));
			}
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
}