import {
    DataciteDoiWidget, DoiDataciteFinder, faMagicIcon, PopupDialogue, propResultFilters, UrlWidget,
    type AnyInputElement,
    type JSONObject,
} from "../loader";

export class AutofillDialoge extends PopupDialogue {

    private formElement: HTMLFormElement = null;
    private dataciteDoiElement: AnyInputElement = null;
    private repoUrlElement: HTMLInputElement = null;
    protected override get title(): string { return "Autofill from External Metadata" }

    private onSubmit(e: Event): void {
        e.preventDefault();
        console.log("Not Implemented");
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
    }
}

(window as any).openAutofillDialogue = AutofillDialoge.openAutofillDialogue.bind(AutofillDialoge);