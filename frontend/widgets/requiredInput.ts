/** */

import { Widget } from "../loader";

export const requirementAttribute = "data-hssi-required";

export const invalidRecStyle = "invalid-recommended";
export const invalidManStyle = "invalid-mandatory";

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
	public requirementLevel: RequirementLevel = RequirementLevel.OPTIONAL;
	
	public constructor(element: FormElement, requirementLevel: RequirementLevel) {
		this.element = element;
		this.requirementLevel = requirementLevel;
	}

	public onFocusEnter(e: FocusEvent): void {
		// remove invalid style
		let className = "";
		switch(this.requirementLevel) {
			case RequirementLevel.RECOMMENDED: className = invalidRecStyle; break;
			case RequirementLevel.MANDATORY: className = invalidManStyle; break;
		}
		this.element.classList.remove(className);
	}

	public onFocusExit(e: FocusEvent): void {
		
		// no need to add invalid styles if it is filled out
		if(this.element.checkValidity()) return;

		// add invalid style
		let className = "";
		switch(this.requirementLevel) {
			case RequirementLevel.RECOMMENDED: className = invalidRecStyle; break;
			case RequirementLevel.MANDATORY: className = invalidManStyle; break;
		}
		this.element.classList.add(className);
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