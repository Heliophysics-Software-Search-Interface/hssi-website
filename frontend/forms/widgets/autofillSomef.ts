import { 
	FormGenerator, InputWidget, Spinner, ConfirmDialogue 
} from "../../loader";

export const describeApiEndpoint = "/api/describe_form";
export const faMagicIcon = "<i class='fa fa-magic'></i>";

export class AutofillSomefWidget extends InputWidget {

	public getInputType(): string { return "url"; }

	public override initialize(readOnly: boolean = false): void {
		super.initialize(readOnly);
		if(readOnly) return;
		setTimeout(()=>{
			this.parentField?.containerElement?.addEventListener(
				"focusout", async e => {
					this.setValue(this.getInputValue());
					if(!FormGenerator.isAutofilledRepo() && this.parentField.hasValidInput()){
						if(await ConfirmDialogue.getConfirmation(
							"'" + this.getInputValue() + "'\n" +
							"This is the repository we will use to auto-fill " +
							"this form as much as possible. Please check for " + 
							"accuracy. ",
							"Auto-Fill Confirmation",
						)) this.handleAutofill();
					}
				});
		}, 0);
	}

	public override setValue(value: string): void {
		if(value.endsWith(".git")){
			value = value.substring(0, value.length - 4);
		}
		super.setValue(value);
	}

	private async handleAutofill(): Promise<void> {

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
			FormGenerator.markAutofilledRepo();
			Spinner.hideSpinner();
		} 

		catch (e) {
			Spinner.hideSpinner();
			console.error(`Error fetching metadata from ${targetUrl}:`, e);
		}
	}
}