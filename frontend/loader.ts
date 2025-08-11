/**
 * Handles loading modules in the correct order and funnelling them out, 
 * preventing circular dependencies and clearly defining the depedency tree.
 * All modules should be imported from this module, instead of from the file 
 * where they are defined.
 */

export * from "./util";
export * from "./simpleEvent";

export * from "./ui/jsonView";
export * from "./ui/spinner";
export * from "./ui/popupDialogue";
export * from "./ui/confirmDialogue";
export * from "./ui/autofillDialogue";
export * from "./ui/apiQueryPopup";
export * from "./ui/rorFinder";
export * from "./ui/orcidFinder";
export * from "./ui/doiDataciteFinder";

export * from "./forms/fieldRequirement";
export * from "./forms/widgets/widget";
export * from "./forms/widgets/basicWidgets";
export * from "./forms/widgets/modelBox";
export * from "./forms/widgets/findIdWidget";
export * from "./forms/widgets/autofillSomef";
export * from "./forms/widgets/autofillDatacite";

export * from "./forms/fields/modelFieldStructure";
export * from "./forms/fields/modelSubfield";
export * from "./forms/fields/modelMultisubfield";
export * from "./forms/formSubmission";
export * from "./forms/formGenerator";