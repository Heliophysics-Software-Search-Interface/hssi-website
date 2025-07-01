import {
    AutofillDataciteWidget,
    DataciteDoiWidget, describeApiEndpoint, DoiDataciteFinder, faMagicIcon, FormGenerator, PopupDialogue, propResultFilters, Spinner, UrlWidget,
    type AnyInputElement,
    type JSONObject,
} from "../loader";

export class AutofillDialoge extends PopupDialogue {

    private formElement: HTMLFormElement = null;
    private dataciteDoiElement: AnyInputElement = null;
    private repoUrlElement: HTMLInputElement = null;
    protected override get title(): string { return "Autofill from External Metadata" }

    private async onSubmit(e: Event): Promise<void> {
        e.preventDefault();

        const dataciteDoiVal = this.dataciteDoiElement.value.trim();
        const repoUrlVal = this.repoUrlElement.value.trim();
        if(!dataciteDoiVal && !repoUrlVal) return;

        PopupDialogue.hidePopup();
        
        if(dataciteDoiVal){
            Spinner.showSpinner();
            try{
                AutofillDataciteWidget.autofillFromApiData(
                    await AutofillDataciteWidget.getApiDataFromDoi(dataciteDoiVal)
                );
            }
            catch(e) { console.error(e); }
            Spinner.hideSpinner();
            FormGenerator.fillForm({
                persistentIdentifier: dataciteDoiVal
            });
        }

        if(repoUrlVal){
            Spinner.showSpinner("Fetching metadata from repository, this may take a moment");
            try{
                const requestUrl = describeApiEndpoint + `?target=${repoUrlVal}`
                const data = await (await fetch(requestUrl)).json();
                console.log(`described repo at ${repoUrlVal}`, data);
                FormGenerator.fillForm(data);
            }
            catch(e){ console.error(e); }
            Spinner.hideSpinner();
            FormGenerator.fillForm({
                codeRepositoryURL: repoUrlVal
            });
        }
    }

    private onShown(): void {
        this.dataciteDoiElement.value = "";
        this.dataciteDoiElement.data = null;
        this.repoUrlElement.value = "";
    }

    protected override createContent(): void {
        super.createContent();
        const content = this.contentElement;
        const form = document.createElement("form");

        const doiLabel = document.createElement("label");
        doiLabel.innerText = "DOI";
        const doiElem = document.createElement("input");

        const findDoiButton = document.createElement("button");
        findDoiButton.type = "button";
        findDoiButton.innerHTML = faMagicIcon + " find";
        findDoiButton.addEventListener("click", e => {
            PopupDialogue.showPopup(
                DoiDataciteFinder.getInstance()
                    .setTarget(doiElem)
                    .withFilters(["software", "concept"])
            );
        });
        
        const repoLabel = document.createElement("label");
        repoLabel.innerText = "Repository URL";
        const repoElem = document.createElement("input");
        
        const submitButton = document.createElement("button");
        submitButton.innerText = "autofill";
        submitButton.type = "submit";
        
        form.addEventListener("submit", e => this.onSubmit(e));
        this.formElement = form;
        this.dataciteDoiElement = doiElem;
        this.repoUrlElement = repoElem;

        form.appendChild(doiLabel);
        form.appendChild(doiElem);
        form.appendChild(findDoiButton);
        form.appendChild(repoLabel);
        form.appendChild(repoElem);
        form.appendChild(submitButton);
        content.appendChild(form);

        this.onShow.addListener(() => this.onShown());
    }

    /// Static -----------------------------------------------------------------

    public static instance: AutofillDialoge = null;

    public static validateInstance(): void {
        if(this.instance == null) this.instance = new AutofillDialoge();
    }

    public static openAutofillDialogue(): void {
        this.validateInstance();
        PopupDialogue.showPopup(this.instance);
        console.log("open aoutofill dialogue");
    }
}

(window as any).openAutofillDialogue = AutofillDialoge.openAutofillDialogue.bind(AutofillDialoge);