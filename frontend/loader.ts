/**
 * Handles loading modules in the correct order and funnelling them out, 
 * preventing circular dependencies and clearly defining depedency tree.
 * All modules should be imported from this file, not directly from the file 
 * where they are defined.
 */

export { Widget } from "./widgets/widget";
export { ModelObjectSelector } from "./widgets/modelObjectSelector";