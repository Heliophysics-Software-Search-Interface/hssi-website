/**
 * entry point module for the website frontend logic
 */

import { 
	FieldRequirement, Widget, ModelBox, ModelObjectSelector
} from "./loader";

function main() {
	
	// register widgets that can be generated on clientside
	Widget.registerWidgets(
		ModelBox,
		ModelObjectSelector,
	)

	// initialize all widgets
	Widget.initializeWidgets(ModelBox);
	Widget.initializeWidgets(ModelObjectSelector);

	// apply the requirement levels for the form widget requirements
	setTimeout(() => FieldRequirement.applyRequirementLevels(), 1000);
}

// call main when document DOM tree is finished building so that we can access
// all elements we need
document.addEventListener("DOMContentLoaded", main);