/**
 * entry point module for the website frontend logic
 */

import { 
	// widgets to initialize
	CharWidget, NumberWidget, UrlWidget, EmailWidget, DateWidget, 
	TextAreaWidget, CheckboxWidget, Widget, AutofillSomefWidget, 
	ModelBox, FormGenerator, RorWidget, OrcidWidget, DataciteDoiWidget,
	AutofillDataciteWidget, AutofillDialoge,

	// dialogues
	RorFinder, OrcidFinder, DoiDataciteFinder,
	ConfirmDialogue, TextInputDialogue, 
} from "./loader";

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
		ModelBox,
		AutofillSomefWidget,
		AutofillDataciteWidget,
	)

	// generate the forms
	FormGenerator.generateForm(null);
}

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