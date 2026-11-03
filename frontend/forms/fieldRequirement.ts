/**
 * Requirement levels for form fields and the logic that highlights a field and
 * shows a note under it when it is invalid or left empty. Touch this when
 * changing how required, recommended, or invalid fields are flagged.
 *
 * @module
 */

import { 
	ModelBox,
	ModelMultiSubfield,
	type ModelSubfield,
} from "../loader";

/** `"data-hssi-required"`: attribute holding an element's requirement level. */
export const requirementAttribute = "data-hssi-required";
/**
 * `"data-hssi-required-container"`: attribute a widget's element gets holding
 * its requirement level.
 */
export const requirementAttributeContainer = "data-hssi-required-container";

/**
 * `"invalid-recommended"`: CSS class for an empty or invalid recommended field.
 */
export const invalidRecStyle = "invalid-recommended";
/**
 * `"invalid-mandatory"`: CSS class for an empty mandatory field, or any field
 * with an invalid value.
 */
export const invalidManStyle = "invalid-mandatory";
/** `"note"`: CSS class for the warning note shown under a field. */
export const noteStyle = "note"

/**
 * Enum of how required a field is: `OPTIONAL` (0), `RECOMMENDED` (1),
 * `MANDATORY` (2, blocks submission).
 */
export enum RequirementLevel {
	/** its optional - unnecessary if not relevant */
	OPTIONAL = 0,
	/** its recommended to not be left blank */
	RECOMMENDED = 1,
	/** it must be filled or else the form cannot be submitted */
	MANDATORY = 2,
}

/**
 * Tracks a field's requirement level and applies or removes its warning styles
 * and note as focus leaves or enters the field.
 */
export class FieldRequirement {

	private _focusEnterListener: Function = null;
	private _focusExitListener: Function = null;
	private _mouseupListener: Function = null;
	private _eventTarget: HTMLElement = null;

	/** The `ModelSubfield` this requirement applies to. */
	public field: ModelSubfield = null;
	/** Element that receives the warning styles and focus listeners. */
	public containerElement: HTMLElement = null;
	/** The warning note element placed after the styled element. */
	public noteElement: HTMLDivElement = null;
	/** The field's `RequirementLevel`. */
	public level: RequirementLevel = RequirementLevel.OPTIONAL;
	
	/**
	 * Binds to the field's container, creates the hidden note element, and adds
	 * focus listeners.
	 */
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
		if(!this.field.hasValidFormatValue()) note = "Invalid";
		else switch(this.level){
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

		let vNote = this.field.getInputElement()?.validationMessage ?? "";
		let fields = (this.field as ModelMultiSubfield).multiFields || [this.field];
		for(const field of fields){
			if(field.widget instanceof ModelBox){
				if(!field.widget.properties.allowNewEntries){
					if(!field.getInputElement().data){
						vNote = "Please select an item from the dropdown list";
					}
				}
			}
		}
		
		if(note.length > 0 && vNote.length > 0) {
			note += " - " + vNote;
			if(this.level < RequirementLevel.MANDATORY) {
				" (Or leave blank if not applicable)";
			}
		}

		return note;
	}

	/** Removes the warning styles and hides the note. */
	public removeStyles(): void {
		let elem = this.getStyledElement();
		for(const stylename of [invalidRecStyle, invalidManStyle]){
			elem.classList.remove(stylename);
			this.noteElement.classList.remove(stylename);
		}
		this.noteElement.style.display = "none";
	}

	private applyStyles(forceMandatoryStyle: boolean = false): void {

		// decide which style to use
		let className = "";
		if(forceMandatoryStyle) className = invalidManStyle;
		else switch(this.level) {
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
		else this.applyStyles(!this.field.hasValidFormatValue());
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

	/** Runs `applyRequirementWarningStyles` on every registered requirement. */
	public static applyStylesForAll(): void {
		for(const req of FieldRequirement.all) {
			req.applyRequirementWarningStyles();
		}
	}
}