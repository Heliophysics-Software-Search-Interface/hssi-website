import { 
    PopupDialogue, ModelSubfield, Spinner, ModelMultiSubfield,
    type JSONValue,
} from '../loader';

const styleResultBox = "hssi-query-results";
const styleRow = "row";
const styleColumn = "column";
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
    protected queryInputElement!: HTMLInputElement;
    protected resultBox!: HTMLDivElement;

    protected abstract get endpoint(): string;

    protected constructor() { super(); }

    public override get title(): string {
        return "Find Item";
    }

    protected override createContent(): void {
        super.createContent();
        this.createQueryForm();
        this.createResultBox();
        this.onShow.addListener(() => {
            this.queryInputElement.focus();
            this.queryInputElement.value = "";
            this.clearResults();
        });
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
        row.classList.add(styleRow);

        const leftColumn = document.createElement("div") as HTMLDivElement;
        leftColumn.classList.add(styleColumn);
        const rightColumn = document.createElement("div") as HTMLDivElement;
        rightColumn.classList.add(styleColumn);

        leftColumn.appendChild(result.textContent);
        
        const link = document.createElement("a") as HTMLAnchorElement;
        link.innerText = result.id;
        link.href = result.id;
        link.target = "_blank";
        leftColumn.appendChild(link);

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
        rightColumn.appendChild(selectButton);

        row.appendChild(leftColumn);
        row.appendChild(rightColumn);
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
            this.centerPopupHorizontally();
            Spinner.hideSpinner(this.resultBox);
        } 
        catch(e) { 
            console.error(e);
            Spinner.hideSpinner(this.resultBox); 
        }
    }

    /** empty all search results from the query search box */
    public clearResults(): void {
        while(this.resultBox.firstChild) {
            this.resultBox.removeChild(this.resultBox.firstChild);
        }
    }
}