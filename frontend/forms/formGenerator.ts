import { 
	typeAttribute, ModelFieldStructure, ModelSubfield, widgetDataAttribute,
	RequirementLevel, ConfirmDialogue, fetchTimeout, labelStyle,
	requiredIndicatorStyle, explanationTextStyle, Spinner,
	type SubmissionFormData, type JSONValue, type JSONObject,
} from "../loader";

const generatedFormType = "generated-form";
const formFieldsType = "form-field-container";
const structureNameData = "fields-structure-name";
const csrfTokenName = "csrfmiddlewaretoken"

const modelStructureUrl = "/api/models/structures/";

export const formRowStyle = "form-row";
export const formSeparatorStyle = "form-separator"

type ModelStructureData = {
	data: ModelFieldStructure[],
	fieldMap: JSONObject,
}

export class FormGenerator {

	private formElement: HTMLFormElement = null;
	private submitElement: HTMLInputElement = null;
	private fieldContainer: HTMLDivElement = null;
	private fields: (ModelSubfield | ModelSubfield[])[] = [];
	private fieldSections: HTMLDetailsElement[] = [];
	private hasAgreement: boolean = true;
	private agreementElement: HTMLInputElement = null;

	public autofilledFromDatacite: boolean = false;
	public autofilledFromRepo: boolean = false;

	private buildForm(): void {

		// don't try to generate the form without structure data
		if(FormGenerator.structureData == null) {
			throw new Error(
				"Form cannot generate without model structure data"
			);
		}

		// generate a row for each field
		let i = 0;

		// TODO generalize the titles somehow
		const titles: string[] = [
			"",
			"Additional Data (click to expand)",
			"Additional Metadata (click to expand)",
			"",
		];
		
		for(const field of this.fields) {
			if(field instanceof Array){
				this.buildFormSection(field, titles.shift(), i > 0);
				i++;
				continue;
			}
			const formRow = document.createElement("div") as HTMLDivElement;
			formRow.classList.add(formRowStyle);
			field.buildInterface(formRow);
			this.fieldContainer.appendChild(formRow);
			i++;
		}

		if(this.hasAgreement) this.buildAgreement();

		// generate submit button
		this.submitElement = document.createElement("input");
		this.submitElement.type = "submit";
		this.submitElement.value = "Submit";
		this.formElement.appendChild(this.submitElement);
	}

	private buildAgreement(): void{
		const div = document.createElement("div");
		
		const header = document.createElement("div");
		header.classList.add(labelStyle);
		header.innerText = "Metadata Agreement ";

		const req = document.createElement("span");
		req.classList.add(requiredIndicatorStyle);
		req.innerText = "*";
		header.appendChild(req);

		const para = document.createElement("div");
		para.classList.add(explanationTextStyle);
		para.innerText = ("By submitting this form, you acknowledge and " + 
			"agree that any metadata you provide is submitted voluntarily " +
			"and becomes part of the public domain. You waive all rights, " +
			"claims, and interests to the submitted metadata, and grant " +
			"unrestricted use, reproduction, modification, and distribution " +
			"rights to the receiving party or its designees." 
		);

		const label = document.createElement("label");
		this.agreementElement = document.createElement("input");
		this.agreementElement.type = "checkbox"
		label.appendChild(this.agreementElement);

		const bold = document.createElement("b");
		bold.innerText = " I agree";
		label.appendChild(bold);
		
		div.appendChild(header);
		div.appendChild(para);
		div.appendChild(label);
		this.formElement.appendChild(div);
	}

	private buildFormSection(
		fields: ModelSubfield[], 
		title: string,
		collapsible: boolean = true,
	): void {

		const details = document.createElement(collapsible ? "details" : "div");
		details.classList.add(formSeparatorStyle);
		const summary = document.createElement("summary");
		summary.innerText = title;
		details.appendChild(summary);

		for(const field of fields) {
			const formRow = document.createElement("div") as HTMLDivElement;
			formRow.classList.add(formRowStyle);
			field.buildInterface(formRow);
			details.appendChild(formRow);
		}

		if(details instanceof HTMLDetailsElement) {
			this.fieldSections.push(details);
		}
		this.fieldContainer.appendChild(details);
	}

	private userHasAgreed(): boolean{
		return !this.hasAgreement || this.agreementElement.checked;
	}

	private onSubmit(e: SubmitEvent): void{

		// we don't want the default html form functionality submiting anything
		e.preventDefault();

		// check to see all required elements are filled out
		if(!this.validateFieldRequirements()) {
			console.log("form fields not valid!");
			return;
		}

		if(!this.userHasAgreed()){
			ConfirmDialogue.getConfirmation(
				"Error - You must agree to the given terms, please check the " +
				"'I agree' checkbox located at the bottom of the form.", 
				"Metadata Agreement", "ok", "cancel"
			);
			return;
		}

		Spinner.showSpinner();

		// submit the data from the form fields as a JSON string
		const data = this.getJsonData();
		const response = fetchTimeout(this.formElement.action, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-CSRFToken": this.getCsrfTokenValue(),
			},
			body: JSON.stringify(data),
		});

		console.log("data submitted!");
		console.log(data);
		
		response.then(response => {
			Spinner.hideSpinner();
			if(response.redirected) window.location.href = response.url;
		});
		response.catch(() => Spinner.hideSpinner());
		response.finally(() => Spinner.hideSpinner());
	}

	private validateFieldRequirements(): boolean {
		const fields = this.getAllRelevantFields();

		let valid = true;
		let firstInvalidField: ModelSubfield = null;
		for(const field of fields){
			field.requirement.applyRequirementWarningStyles();
			if(field.requirement.level >= RequirementLevel.MANDATORY){
				if(!field.hasValidInput()){
					firstInvalidField = firstInvalidField ?? field;
					valid = false;
				}
			}
		}

		firstInvalidField?.containerElement.scrollIntoView({
			behavior: "smooth", 
			block: "start"
		});
		return valid;
	}

	private updateAllFieldValidityStyles(): void {
		const fields = this.getAllRelevantFields();
		for(const field of fields) field.applyValidityStyles();
	}

	private getCsrfTokenValue(): string {
		const token = (
			this.formElement.querySelector(
				`[name=${csrfTokenName}]`
			) as HTMLInputElement
		);
		if(token == null) {
			console.error("CSRF Token not found for form", this);
			return null;
		}
		return token.value;
	}

	private getRootFields(): ModelSubfield[] {
		if(this.fields.length <= 0) return [];
		const fields: ModelSubfield[] = [];

		for(const field of this.fields){
			if(field instanceof Array) fields.push(...field);
			else fields.push(field);
		}

		return fields;
	}

	private getAllRelevantFields(): ModelSubfield[] {
		const rootFields = this.getRootFields();
		const fields: ModelSubfield[] = [];

		for(const rootField of rootFields){
			fields.push(rootField);
			if(
				rootField.requirement.level >= RequirementLevel.MANDATORY && 
				rootField.hasValidInput()
			){
				ModelSubfield.getSubfieldsRecursive(rootField, true, fields);
			}
		}

		return fields;
	}

	private openFieldSections(): void {
		for(const section of this.fieldSections) {
			section.setAttribute("open", "");
		}
	}

	private closeFieldSections(): void {
		for(const section of this.fieldSections) {
			section.removeAttribute("open");
		}
	}

	public getJsonData(): JSONValue{

		// get all subfields into a linear array
		const subfields: ModelSubfield[] = [];
		let outerFields: ModelSubfield[][] = this.fields as any;
		if(outerFields.length > 0 && !(outerFields[0] instanceof Array)) {
			outerFields = [outerFields] as any;
		}
		for(const outerField of outerFields){
			for(const innerField of outerField) subfields.push(innerField);
		}

		// append all field data to an array
		const data: JSONObject = {};
		for(const field of subfields){
			data[field.name] = field.getFieldData();
		}
		
		return data;
	}

	private static instance: FormGenerator = null;
	private static structureData: ModelStructureData = null;
	public static fieldMap: JSONObject = null;

	/** 
	 * generate a form from a given set of fields, or if not specified, tries 
	 * to find json data about fields inside the text
	 */
	public static async generateForm(fields: ModelSubfield[] = null): Promise<void> {

		// warn about singleton resetting
		if(this.instance != null) {
			console.warn("form generator running multiple times on same page");
		}

		// if there is no form, return early
		const form = document.querySelector(
			`form[${typeAttribute}=${generatedFormType}]`
		) as HTMLFormElement;
		if(form == null) return;

		// TODO placeholder form loading icon

		// load structure data
		if(this.structureData == null) {
			const response = await fetchTimeout(modelStructureUrl);
			const data = await response.json();
			const structureData = data as ModelStructureData;
			this.structureData = structureData;
			this.fieldMap = structureData.fieldMap;
			ModelFieldStructure.parseBasicWidgetModels();
			ModelFieldStructure.parseModels(this.structureData.data);
		}
		
		// get references to or create the form elements
		const generator = new FormGenerator();
		generator.formElement = form;
		generator.fieldContainer = generator.formElement.querySelector(
			`div[${typeAttribute}=${formFieldsType}]`
		);
		if (generator.fieldContainer == null) {
			generator.fieldContainer = document.createElement("div");
			generator.fieldContainer.setAttribute(typeAttribute, formFieldsType);
			generator.formElement.appendChild(generator.fieldContainer);
		}
		
		// override form submission event
		form.addEventListener("submit", e => generator.onSubmit(e));

		// get fields from html elements if not specified in function
		if(fields == null) {
			const dataElement: HTMLScriptElement = 
				document.querySelector(
					`script[${widgetDataAttribute}=${structureNameData}]`
				);
			if(dataElement) {
				const content = JSON.parse(dataElement.textContent.trim());
				if(content instanceof Array){
					const fieldSets: ModelSubfield[] = [];
					for(const structureName of content){
						const structure = ModelFieldStructure.getFieldStructure(structureName);
						if(structure == null){
							console.log(`structure is underfined for ${structureName}`);
						}
						const structInstance = structure.generateInstance();
						fieldSets.push([
							structInstance.topField, 
							...structInstance.subFields
						] as any);
					}
					generator.fields = fieldSets as any;
				}
				else{
					const structure = ModelFieldStructure.getFieldStructure(content);
					const fieldInstance = structure.generateInstance();
					const fields = [fieldInstance.topField, ...fieldInstance.subFields];
					generator.fields = fields;
				}
			}
			else console.warn("No field data found in form");
		}
		else generator.fields = fields;

		// apply the singleton instance
		this.instance = generator;
		this.instance.buildForm();
		
	}

	/**
	 * fills the form with all the specified data in the form of {key:value}
	 * where keys represent the field name
	 * @param data the data to fill the form fields with
	 * @param overwrite_values whether or not fields which already have data should be overwritten
	 */
	public static fillForm(
		data: SubmissionFormData, 
		overwrite_values: boolean = false
	): void {

		const fields = this.instance.getRootFields();
		for(const key in data) {
			const value = data[key as keyof typeof data];
			const field = fields.find(f => f.name === key);
			if(field) {
				if (overwrite_values || !field.hasValidInput()) {
					field.fillField(value);
				}
			}
		}
		this.instance.updateAllFieldValidityStyles();
		this.instance.openFieldSections();
	}

	public static getStructureData(): ModelStructureData{
		return this.structureData;
	}

	public static clearForm(): void {
		const fields = this.instance.getRootFields();
		for(const field of fields) {
			field.clearField();
		}
		this.collapseFormFields();
		this.instance.autofilledFromDatacite = false;
		this.instance.autofilledFromRepo = false;
	}

	public static collapseFormFields(): void {
		for(const field of this.instance.getRootFields()){
			field.collapseSubfields();
		}
		this.instance.closeFieldSections();
	}

	public static expandFormFields(): void {
		this.instance.openFieldSections();
		for(const field of this.instance.getRootFields()){
			field.expandSubfields();
		}
	}

	public static async clearFormConfirm(): Promise<void> {
		if(await ConfirmDialogue.getConfirmation()){
			this.clearForm();
			console.log("Form cleared");
		}
		else console.log("Form clear cancelled");
	}

	public static markAutofilledDatacite(): void { 
		this.instance.autofilledFromDatacite = true;
	}

	public static markAutofilledRepo(): void {
		this.instance.autofilledFromRepo = true;
	}
	
	public static isAutofilledDatacite(): boolean { 
		return this.instance.autofilledFromDatacite; 
	}
	
	public static isAutofilledRepo(): boolean { 
		return this.instance.autofilledFromRepo; 
	}
}

const win = window as any;
win.clearGeneratedForm = FormGenerator.clearFormConfirm.bind(FormGenerator);
win.collapseGeneratedForm = FormGenerator.collapseFormFields.bind(FormGenerator);
win.expandGeneratedForm = FormGenerator.expandFormFields.bind(FormGenerator);