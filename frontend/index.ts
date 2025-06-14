/**
 * entry point module for the website frontend logic
 */

import { 
	CharWidget, NumberWidget, UrlWidget, EmailWidget, DateWidget, 
	TextAreaWidget, CheckboxWidget, Widget, AutofillFormUrlWidget, 
	ModelBox, FormGenerator,
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
		ModelBox,
	)

	// generate the forms
	FormGenerator.generateForm(null);
}

// call main when document DOM tree is finished building so that we can access
// all elements we need
document.addEventListener("DOMContentLoaded", main);