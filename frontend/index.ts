/**
 * entry point module for the website frontend logic
 */

import { 
	// widgets to initialize
	CharWidget, NumberWidget, UrlWidget, EmailWidget, DateWidget, 
	TextAreaWidget, CheckboxWidget, Widget, AutofillFormUrlWidget, 
	ModelBox, FormGenerator, RorWidget, OrcidWidget,

	// etc
	RorFinder, OrcidFinder,
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
		ModelBox,
	)

	// generate the forms
	FormGenerator.generateForm(null);

	// TODO smarter initialization
	RorFinder.getInstance();
	OrcidFinder.getInstance();
}

// call main when document DOM tree is finished building so that we can access
// all elements we need
document.addEventListener("DOMContentLoaded", main);