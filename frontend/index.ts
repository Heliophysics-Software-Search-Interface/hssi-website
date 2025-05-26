/**
 * entry point module for the website frontend logic
 */

import { 
	FieldRequirement, CharWidget, UrlWidget, EmailWidget, DateWidget, 
	TextAreaWidget, CheckboxWidget, Widget, ModelBox, ModelObjectSelector,
} from "./loader";

function main() {
	
	// register widgets that can be generated on clientside
	Widget.registerWidgets(
		CharWidget,
		UrlWidget,
		EmailWidget,
		DateWidget,
		CheckboxWidget,
		TextAreaWidget,
		ModelBox,
		ModelObjectSelector,
	)

	// initialize all widgets
	Widget.initializeRegisteredWidgets();

	// apply the requirement levels for the form widget requirements
	setTimeout(() => FieldRequirement.applyRequirementLevels(), 1000);
}

// call main when document DOM tree is finished building so that we can access
// all elements we need
document.addEventListener("DOMContentLoaded", main);