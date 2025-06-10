import { InputWidget, Spinner } from "../../loader";

const describeApiEndpoint = "/api/describe";

export class AutofillFormUrlWidget extends InputWidget {

    protected createElements(): void {
        super.createElements();
        this.createAutofillButton();
    }

    private createAutofillButton(): void {
        const autofillButton = document.createElement("button");
        autofillButton.innerHTML = "<i class='fa fa-magic'></i> autofill";
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
            Spinner.hideSpinner();
        } 

        catch (e) {
            Spinner.hideSpinner();
            console.error(`Error fetching metadata from ${targetUrl}:`, e);
        }
    }
}