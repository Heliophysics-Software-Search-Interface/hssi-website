/**
 * entry point module for the website frontend logic
 */

import { 
	// widgets to initialize
	CharWidget, NumberWidget, UrlWidget, EmailWidget, DateWidget, 
	TextAreaWidget, CheckboxWidget, Widget, AutofillFormUrlWidget, 
	ModelBox, FormGenerator, RorWidget, OrcidWidget, DataciteDoiWidget,

	// etc
	RorFinder, OrcidFinder, DoiDataciteFinder,
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
		AutofillFormUrlWidget,
		RorWidget,
		OrcidWidget,
		DataciteDoiWidget,
		ModelBox,
	)

	// generate the forms
	FormGenerator.generateForm(null);

	// TODO smarter initialization
	RorFinder.getInstance();
	OrcidFinder.getInstance();
	DoiDataciteFinder.getInstance();
}

// call main when document DOM tree is finished building so that we can access
// all elements we need
document.addEventListener("DOMContentLoaded", main);