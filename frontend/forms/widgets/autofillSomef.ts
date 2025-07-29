import { FormGenerator, InputWidget, Spinner } from "../../loader";

export const describeApiEndpoint = "/api/describe_form";
export const faMagicIcon = "<i class='fa fa-magic'></i>";

export class AutofillSomefWidget extends InputWidget {

	protected createElements(): void {
		super.createElements();
		this.createAutofillButton();
	}

	private createAutofillButton(): void {
		const autofillButton = document.createElement("button");
		autofillButton.innerHTML = faMagicIcon + " autofill";
		autofillButton.title = (
			"Fetch metadata from the specified repository " + 
			"and use it to autofill the fields in the form"
		);
		autofillButton.type = "button"; // Prevents form submission
		autofillButton.addEventListener("click", () => this.onPressAutofillButton());
		this.element.appendChild(autofillButton);
	}

	public getInputType(): string { return "url"; }

	private async onPressAutofillButton(): Promise<void> {

		// validate input before sending request
		if(!this.inputElement.checkValidity() || this.inputElement.value.length <= 0){
			console.error(this.inputElement.validationMessage);
			this.parentField.requirement.applyRequirementWarningStyles();
			return;
		}
		
		const targetUrl = this.inputElement.value.trim();
		const requestUrl = describeApiEndpoint + `?target=${targetUrl}`;

		try {
			Spinner.showSpinner("Fetching metadata from repository, this may take a moment");
			const data = await (await fetch(requestUrl)).json();
			console.log(`described repo at ${this.inputElement.value}`, data);
			FormGenerator.fillForm(data);
			FormGenerator.markAutofilledDatacite();
			Spinner.hideSpinner();
		} 

		catch (e) {
			Spinner.hideSpinner();
			console.error(`Error fetching metadata from ${targetUrl}:`, e);
		}
	}
}