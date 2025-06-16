import { 
    PopupDialogue, ModelSubfield, Spinner, ModelMultiSubfield,
    type JSONValue,
} from '../loader';

const styleResultBox = "hssi-query-results";
export const faSearchIcon = "<i class='fa fa-search'></i>";

export type ApiQueryResult = {
    textContent: HTMLDivElement;
    id: string;
}

/**
 * A popup dialogue box that allows the user to search for a specified query 
 * to get an item from an external api such as orcid or ror urls
 */
export abstract class ApiQueryPopup extends PopupDialogue {
    
    protected targetField: ModelSubfield = null;
    protected formElement: HTMLFormElement = null;
    protected queryInputElement: HTMLInputElement = this.queryInputElement ?? null;
    protected resultBox: HTMLDivElement = this.resultBox ?? null;

    protected abstract get endpoint(): string;

    protected constructor() { super(); }

    public override get title(): string {
        return "Find Item";
    }

    protected override createContent(): void {
        super.createContent();
        this.createQueryForm();
        this.createResultBox();
    }

    /** the form which will be used to submit queries to the external api */
    protected createQueryForm(): void {
        this.formElement = document.createElement("form") as HTMLFormElement;
        this.createQueryInput();
        this.formElement.addEventListener("submit", (e: Event) => {
            e.preventDefault();
            const query = this.queryInputElement.value;
            if(query.length > 0) this.submitQuery(query);
        });

        const submit = document.createElement("button") as HTMLButtonElement;
        submit.type = "submit";
        submit.innerHTML = faSearchIcon + " Search";
        this.formElement.appendChild(submit);

        this.contentElement.appendChild(this.formElement);
    }

    protected createQueryInput(): void {
        this.queryInputElement = document.createElement("input") as HTMLInputElement;
        this.queryInputElement.type = "text";
        this.formElement.appendChild(this.queryInputElement);
    }

    protected createResultBox(): void {
        this.resultBox = document.createElement("div") as HTMLDivElement;
        this.resultBox.classList.add(styleResultBox);
        this.contentElement.appendChild(this.resultBox);
    }

    protected abstract getQueryResults(query: string): Promise<JSONValue>;

    protected abstract handleQueryResults(results: JSONValue): void;

    protected addResultRow(result: ApiQueryResult): void {
        const row = document.createElement("div") as HTMLDivElement;
        row.appendChild(result.textContent);
        
        const link = document.createElement("a") as HTMLAnchorElement;
        link.href = result.id;
        link.target = "_blank";
        row.appendChild(link);

        const selectButton = document.createElement("button") as HTMLButtonElement;
        selectButton.type = "button";
        selectButton.innerHTML = "Select";
        selectButton.addEventListener("click", () => {
            if(!this.targetField.multi){
                this.targetField.getInputElement().value = result.id;
            }
            else if (this.targetField instanceof ModelMultiSubfield){
                this.targetField.addNewMultifieldWithValue(result.id);
            }
            PopupDialogue.hidePopup();
        });
        row.appendChild(selectButton);

        this.resultBox.appendChild(row);
    }

    /** submit a query to the api to fetch some search results */
    public async submitQuery(query: string): Promise<void> {
        this.clearResults();
        Spinner.showSpinner("", this.resultBox);
        try{
            const results = await this.getQueryResults(query);
            console.log("Query results: ", results);
            this.handleQueryResults(results);
            Spinner.hideSpinner(this.resultBox);
        } 
        catch(e) { 
            console.error(e);
            Spinner.hideSpinner(this.resultBox); 
        }
    }

    /** empty all search results from the query search box */
    public clearResults(): void {
        for(const row of this.resultBox.children){
            row.remove();
        }
    }
}