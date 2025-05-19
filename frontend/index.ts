/**
 * entry point module for the website frontend logic
 */

import { Widget } from "./loader";
import { ModelObjectSelector } from "./loader";

function main() {
	// initialize all widgets
	Widget.initializeWidgets(ModelObjectSelector);
}

// call main when document DOM tree is finished building so that we can access
// all elements we need
document.addEventListener("DOMContentLoaded", main);