/**
 * entry point module for the website frontend logic
 */

import { 
	// widgets to initialize
	CharWidget, NumberWidget, UrlWidget, EmailWidget, DateWidget, 
	TextAreaWidget, CheckboxWidget, Widget, AutofillSomefWidget, 
	ModelBox, FormGenerator, RorWidget, OrcidWidget, DataciteDoiWidget,
	AutofillDataciteWidget,

	// etc
	RorFinder, OrcidFinder, DoiDataciteFinder,
	ConfirmDialogue, 
} from "./loader";

function main() {
	
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

	// TODO smarter initialization
	ConfirmDialogue.validateInstance();
	RorFinder.getInstance();
	OrcidFinder.getInstance();
	DoiDataciteFinder.getInstance();
}

// call main when document DOM tree is finished building so that we can access
// all elements we need
document.addEventListener("DOMContentLoaded", main);