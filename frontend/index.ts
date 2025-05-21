/**
 * entry point module for the website frontend logic
 */

import { RequiredInput, Widget, ModelObjectSelector } from "./loader";

function main() {
	// initialize all widgets
	Widget.initializeWidgets(ModelObjectSelector);
	setTimeout(() => RequiredInput.applyRequirementLevels(), 1000);
}

// call main when document DOM tree is finished building so that we can access
// all elements we need
document.addEventListener("DOMContentLoaded", main);