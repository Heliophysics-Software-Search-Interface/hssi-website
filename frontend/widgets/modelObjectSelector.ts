/**
 * Handles model object selector widgets frontend logic
 */

import { Widget } from "../loader";

export class ModelObjectSelector extends Widget {
	
	/** collection of all the initialized widgets */
	public static widgets: Array<ModelObjectSelector> = []

	protected initialize(): void {
		console.log("Initializing model object selector..");
		ModelObjectSelector.widgets.push(this);
	}

}