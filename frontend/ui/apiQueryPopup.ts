import { 
    PopupDialogue, ModelSubfield, Spinner, ModelMultiSubfield,
    type JSONValue,
    type JSONObject,
    fetchTimeout,
    type JSONArray,
    type DataciteItem,
    type AnyInputElement,
} from '../loader';

const styleResultBox = "hssi-query-results";
const styleRow = "row";
const styleColumn = "column";
export const faSearchIcon = "<i class='fa fa-search'></i>";
export const propResultFilters = "resultFilters";

export type ApiQueryResult = {
    jsonData: JSONObject;
    textContent: HTMLDivElement;
    id: string;
}

/**
 * A popup dialogue box that allows the user to search for a specified query 
 * to get an item from an external api such as orcid or ror urls
 */
export abstract class ApiQueryPopup extends PopupDialogue {
    
    protected targetField: ModelSubfield | AnyInputElement = null;
    protected formElement: HTMLFormElement = null;
    protected queryInputElement: HTMLInputElement = null;
    protected resultBox: HTMLDivElement = null;
    protected filters: string[] = [];
    private isBusy: boolean = false;

    protected get contentType(): string { return "application/json" };

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
            setTimeout(() => this.queryInputElement.focus(), 0);
            this.clearResults();
        });
        this.onHide.addListener(() => {
            this.queryInputElement.value = "";
            this.filters.length = 0;
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
        this.queryInputElement.placeholder = "Enter search term"
        this.formElement.appendChild(this.queryInputElement);
    }

    protected createResultBox(): void {
        this.resultBox = document.createElement("div") as HTMLDivElement;
        this.resultBox.classList.add(styleResultBox);
        this.contentElement.appendChild(this.resultBox);
    }

    protected abstract getQueryUrl(query: string): string;

    protected getRequestHeaders(): Record<string, string> {
        return { "Content-Type": this.contentType };
    }

    protected async getQueryResults(query: string): Promise<JSONValue> {
        if(this.isBusy){
            throw new Error("Busy - Cannot send requests right now!");
        }
        
        this.isBusy = true;
        try{
            const response = await fetchTimeout(this.getQueryUrl(query), {
                method: "GET",
                headers: this.getRequestHeaders(),
            });
            const data = await response.json();
            this.isBusy = false;

            if (!response.ok) {
                throw new Error(`Error fetching data: ${response.status} ${response.statusText}`);
            }
            return data;
        }
        catch(e) {
            this.isBusy = false;
            throw(e);
        }
    }

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
            if(this.targetField instanceof HTMLElement){
                const inputElem = this.targetField as AnyInputElement;
                inputElem.value = result.id;
                inputElem.data = result.jsonData;
                PopupDialogue.hidePopup();
                return;
            }
            else if(!this.targetField.multi){
                const inputElem = this.targetField.getInputElement();
                inputElem.value = result.id;
                inputElem.data = result.jsonData;
            }
            else if (this.targetField instanceof ModelMultiSubfield){
                this.targetField.addNewMultifieldWithValue(result.id);
            }
            this.targetField.requirement.applyRequirementWarningStyles();
            PopupDialogue.hidePopup();
        });
        rightColumn.appendChild(selectButton);

        row.appendChild(leftColumn);
        row.appendChild(rightColumn);
        this.resultBox.appendChild(row);
    }

    /// filtering results ------------------------------------------------------

    protected filterResults(results_in: JSONArray): JSONArray{
        console.log(`Filtering ${results_in.length} results...`);
        let results = results_in;
        for(const filter of this.filters){
            console.log(`Applying ${filter} filter`);
            results = (
                (this as any)
                [`resultsFiltered_${filter}`] as (x:JSONArray)=>JSONArray
            )(results);
            console.log(results);
        }
        console.log("Filtered results", results);
        return results;
    }

    protected resultsFiltered_software(
        results_in: JSONArray<DataciteItem>
    ): JSONArray<DataciteItem>{
        return results_in.filter(x => {
            return x.attributes?.types?.resourceTypeGeneral === "Software";
        });
    }

    protected resultsFiltered_concept(
        results_in: JSONArray<DataciteItem>
    ): JSONArray<DataciteItem> {
        return results_in.filter(x => {
            if(x.attributes?.relatedIdentifiers){
                for(const relId of x.attributes.relatedIdentifiers){
                   if (relId.relationType === "IsVersionOf") return false;
                   if (relId.relationType === "HasVersion") return true;
                }
            }
            return true;
        });
    }

    /** submit a query to the api to fetch some search results */
    public async submitQuery(query: string): Promise<void> {
        if(this.isBusy) {
            console.warn("Attempt to submit query while busy");
            return;
        }
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

    public setTarget(
        field: ModelSubfield | AnyInputElement, 
        useParentField: boolean = true
    ): ApiQueryPopup {
        this.targetField = field;
        if (field instanceof ModelSubfield && useParentField && field.parent) {
            this.withQuery(field.parent.getInputElement().value.trim());
        }
        return this;
    }

    public withQuery(query: string): ApiQueryPopup {
        this.queryInputElement.value = query;
        if(query) this.submitQuery(query);
        return this;
    }

    public withFilters(filters: string[]): ApiQueryPopup {
        if(filters) this.filters.push(...filters);
        return this;
    }

    /** empty all search results from the query search box */
    public clearResults(): void {
        while(this.resultBox.firstChild) {
            this.resultBox.removeChild(this.resultBox.firstChild);
        }
    }
}