/**
 * entry point module for the website frontend logic
 */

import { 
	FieldRequirement, CharWidget, NumberWidget, UrlWidget, EmailWidget, 
	DateWidget, TextAreaWidget, CheckboxWidget, Widget, ModelBox, FormGenerator,
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
		ModelBox,
	)

	// generate the forms
	FormGenerator.generateForm(null);

	// apply the requirement levels for the form widget requirements
	// TODO test and remove if the deferred call is needed, remove if not
	setTimeout(() => FieldRequirement.applyRequirementLevels(), 1000);
}

// call main when document DOM tree is finished building so that we can access
// all elements we need
document.addEventListener("DOMContentLoaded", main);