/**
 * entry point module for the website frontend logic
 *
 * Touch this when registering a new client-side widget or dialogue.
 *
 * @module
 */

import {
	// widgets to initialize
	CharWidget, NumberWidget, UrlWidget, EmailWidget, DateWidget,
	TextAreaWidget, CheckboxWidget, Widget, AutofillSomefWidget,
	ModelBox, FormGenerator, RorWidget, OrcidWidget, DataciteDoiWidget,
	AutofillDataciteWidget, AutofillDialoge, AuthorIdentifierWidget,

	// dialogues
	RorFinder, OrcidFinder, DoiDataciteFinder,
	ConfirmDialogue, TextInputDialogue,
} from "./loader";

/**
 * Registers the widget types that can be generated client-side (basic input
 * widgets, `RorWidget`, `OrcidWidget`, `DataciteDoiWidget`,
 * `AuthorIdentifierWidget`, `ModelBox` and the autofill widgets), then
 * generates the form. Exposed on `window`.
 */
function initForms() {
	
	// register widgets that can be generated on clientside
	Widget.registerWidgets(
		CharWidget,
		NumberWidget,
		UrlWidget,
		EmailWidget,
		DateWidget,
		CheckboxWidget,
		TextAreaWidget,
		RorWidget,
		OrcidWidget,
		DataciteDoiWidget,
		AuthorIdentifierWidget,
		ModelBox,
		AutofillSomefWidget,
		AutofillDataciteWidget,
	)

	// generate the forms
	FormGenerator.generateForm(null);
}

/**
 * Creates the shared dialogue instances: confirm, autofill and text input
 * dialogues, and the ROR, ORCID and DataCite DOI finders. Exposed on `window`.
 */
function initDialogue() {
	ConfirmDialogue.validateInstance();
	AutofillDialoge.validateInstance();
	TextInputDialogue.validateInstance();
	RorFinder.getInstance();
	OrcidFinder.getInstance();
	DoiDataciteFinder.getInstance();
}

const win = window as any;
win.initDialogue = initDialogue;
win.initForms = initForms;