/** */

import { 
	type ModelSubfield,
} from "../loader";

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

export class FieldRequirement {

	private _focusEnterListener: Function = null;
	private _focusExitListener: Function = null;
	private _mouseupListener: Function = null;
	private _eventTarget: HTMLElement = null;

	public field: ModelSubfield = null;
	public containerElement: HTMLElement = null;
	public noteElement: HTMLDivElement = null;
	public level: RequirementLevel = RequirementLevel.OPTIONAL;
	
	public constructor(
		field: ModelSubfield,
		requirementLevel: RequirementLevel,
	) {
		this.field = field;
		this.containerElement = field.containerElement;
		this.level = requirementLevel;
		this.createNoteElement();
		this.addEventListeners();
		FieldRequirement.all.push(this);
	}

	/// Private methods --------------------------------------------------------

	/** add focus event listeners */ 
	private addEventListeners(): void {

		const focusIn = (e: FocusEvent) => {
			this.onFocusEnter(e);
		};
		const focusout = (e: FocusEvent) => {
			this.onFocusExit(e);
		};
		this._focusEnterListener = focusIn;
		this._focusExitListener = focusout;
		
		this.containerElement.addEventListener("focusin", focusIn);
		this.containerElement.addEventListener("focusout", focusout);
		this._eventTarget = this.containerElement;
	}

	private createNoteElement(): void {
		this.noteElement = document.createElement("div");
		this.noteElement.classList.add(noteStyle);
		this.noteElement.style.display = "none";
		this.getStyledElement().insertAdjacentElement("afterend", this.noteElement);
	}

	private getNoteText(): string {
		const valid = this.field.hasValidInput();
		if(valid || this.level == RequirementLevel.OPTIONAL) return "";

		let note = "";
		switch(this.level){
			case RequirementLevel.MANDATORY: 
				note = "Mandatory";
				break;
			case RequirementLevel.RECOMMENDED: 
				note = "Recommended";
				break;
			default:
				note = "Invalid";
				break;
		}

		const vNote = this.field.getInputElement()?.validationMessage ?? "";
		if(note.length > 0 && vNote.length > 0) {
			note += " - " + vNote;
			if(this.level < RequirementLevel.MANDATORY) {
				"(Or leave blank if not applicable)";
			}
		}

		return note;
	}

	public removeStyles(): void {
		let className = "";
		switch(this.level) {
			case RequirementLevel.RECOMMENDED: className = invalidRecStyle; break;
			case RequirementLevel.MANDATORY: className = invalidManStyle; break;
		}
		if(className.length > 0){
			this.getStyledElement().classList.remove(className);
			this.noteElement.classList.remove(className);
		}
		this.noteElement.style.display = "none";
	}

	private applyStyles(): void {

		// add invalid style
		let className = "";
		switch(this.level) {
			case RequirementLevel.RECOMMENDED: className = invalidRecStyle; break;
			case RequirementLevel.MANDATORY: className = invalidManStyle; break;
			default: return;
		}

		// add class to required element/container if applicable
		this.getStyledElement().classList.add(className);
		this.noteElement.classList.add(className);
		this.noteElement.style.display = "block";
		this.noteElement.innerText = this.getNoteText();
	}

	private hasFocus(): boolean {
		return this._eventTarget.contains(document.activeElement);
	}

	/// Public methods ---------------------------------------------------------

	/** returns the element that the invalid-* class style is applied to */
	public getStyledElement(): HTMLElement {
		return this.containerElement;
	}

	/** destroy object and remove elements from dom */
	public destroy(): void{

		// remove event listeners
		if(this._focusEnterListener != null) {
			this._eventTarget.removeEventListener(
				"focusin", 
				this._focusEnterListener as any
			);
			this._focusEnterListener = null;
		}
		if(this._focusExitListener != null){
			this._eventTarget.removeEventListener(
				"focusout", 
				this._focusExitListener as any
			);
			this._focusExitListener = null;
		}

		this.removeStyles();
		let index = FieldRequirement.all.indexOf(this);
		if (index >= 0) FieldRequirement.all.splice(index, 1);
		this.noteElement?.remove();
	}

	/** 
	 * highlight and put warning message on field if applicable or removes 
	 * it if it shouldn't be there 
	 */
	public applyRequirementWarningStyles(): void{
		if(this.field.hasValidInput()) this.removeStyles();
		else this.applyStyles();
	}

	/// Event listeners --------------------------------------------------------

	private onFocusEnter(_e: FocusEvent): void {
		// remove invalid style
		this.removeStyles();
	}

	private onFocusExit(_e: FocusEvent): void {

		// TODO apply styles on mouseup instead of here

		if(this._mouseupListener != null){
			window.removeEventListener("mouseup", this._mouseupListener as any);
		}

		const mouseup = (e: MouseEvent) => {
			if(!this.hasFocus()) this.applyRequirementWarningStyles();
			window.removeEventListener("mouseup", this._mouseupListener as any);
			this._mouseupListener = null;
		};

		window.addEventListener("mouseup", mouseup)
		this._mouseupListener = mouseup;
	}

	/// Static properties ------------------------------------------------------

	/** 
	 * contains all required widgets in a given form with a requirement level 
	 * greater than OPTIONAL
	*/
	private static all: FieldRequirement[] = [];

	/// Static methods ---------------------------------------------------------

	public static applyStylesForAll(): void {
		for(const req of FieldRequirement.all) {
			req.applyRequirementWarningStyles();
		}
	}
}