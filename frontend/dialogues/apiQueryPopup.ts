/**
 * The abstract base for popups that search an external API (ORCID, ROR,
 * DataCite) and let the user pick a result to fill into a form field. Touch
 * this when writing a new external-lookup popup or changing how results are
 * listed, filtered or selected.
 *
 * @module
 */

import { 
	PopupDialogue, ModelSubfield, Spinner, ModelMultiSubfield,
	type JSONValue,
	type JSONObject,
	fetchTimeout,
	type JSONArray,
	type DataciteItem,
	type AnyInputElement,
	FindIdWidget,
	FormGenerator,
} from '../loader';

const styleResultBox = "hssi-query-results";
const styleRow = "row";
const styleColumn = "column";
/** Font Awesome search icon HTML. */
export const faSearchIcon = "<i class='fa fa-search'></i>";
/**
 * `"resultFilters"`: widget property naming the result filters to pass to
 * `withFilters`.
 */
export const propResultFilters = "resultFilters";

/** One search result: its JSON data, a display element, and its ID URL. */
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
	
	/** The `ModelSubfield` or input element a selected result is written to. */
	protected targetField: ModelSubfield | AnyInputElement = null;
	/** The query form. */
	protected formElement: HTMLFormElement = null;
	/** The query text input. */
	protected queryInputElement: HTMLInputElement = null;
	/** Container for the result rows. */
	protected resultBox: HTMLDivElement = null;
	/** Names of the result filters to apply; cleared when the popup hides. */
	protected filters: string[] = [];
	private isBusy: boolean = false;
	
	/** Optional text shown above the form; empty by default. */
	protected get description(): string { return "" };
	/** Request `Content-Type`; `"application/json"` by default. */
	protected get contentType(): string { return "application/json" };

	/** The API endpoint. */
	protected abstract get endpoint(): string;

	/** Calls the `PopupDialogue` constructor. */
	protected constructor() { super(); }

	/** Overrides to return `"Find Item"`. */
	public override get title(): string {
		return "Find Item";
	}

	/**
	 * Overrides to add the description, query form and result box, focusing the
	 * input and clearing results on show and resetting the query and filters on
	 * hide.
	 */
	protected override createContent(): void {
		super.createContent();
		if(this.description){
			const descElem = document.createElement("p");
			descElem.innerText = this.description;
			this.contentElement.appendChild(descElem);
		}
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

	/** Creates the query text input. */
	protected createQueryInput(): void {
		this.queryInputElement = document.createElement("input") as HTMLInputElement;
		this.queryInputElement.type = "text";
		this.queryInputElement.placeholder = "Enter search term"
		this.formElement.appendChild(this.queryInputElement);
	}

	/** Creates the result container. */
	protected createResultBox(): void {
		this.resultBox = document.createElement("div") as HTMLDivElement;
		this.resultBox.classList.add(styleResultBox);
		this.contentElement.appendChild(this.resultBox);
	}

	/** The request URL for a query. */
	protected abstract getQueryUrl(query: string): string;

	/** Request headers; sets `Content-Type` from `contentType`. */
	protected getRequestHeaders(): Record<string, string> {
		return { "Content-Type": this.contentType };
	}

	/**
	 * Fetches the query URL and returns the JSON response; throws if a request
	 * is already in progress or the response is not OK.
	 */
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

	/** Turns the API response into result rows. */
	protected abstract handleQueryResults(results: JSONValue): void;

	/**
	 * Adds a result row with a link and a Select button that writes the result
	 * to the target field and closes the popup.
	 */
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
			else if(this.targetField instanceof ModelSubfield) {
				this.targetField.setValue(result.id);
				const targetWidget = this.targetField.widget;
				if(targetWidget instanceof FindIdWidget){
					targetWidget.onDataSelected(result.jsonData);
					targetWidget.getInputElement().focus();
				}
				if(!this.targetField.multi){
					const inputElem = this.targetField.getInputElement();
					inputElem.value = result.id;
					inputElem.data = result.jsonData;
				}
				else if (this.targetField instanceof ModelMultiSubfield){
					this.targetField.addNewMultifieldWithValue(result.id);
				}
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

	/**
	 * Applies each filter in `filters` by calling the matching
	 * `resultsFiltered_<name>` method.
	 */
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

	/** Keeps DataCite results of type `Software`. */
	protected resultsFiltered_software(
		results_in: JSONArray<DataciteItem>
	): JSONArray<DataciteItem>{
		return results_in.filter(x => {
			return x.attributes?.types?.resourceTypeGeneral === "Software";
		});
	}

	/** Removes DataCite results of type `Software`. */
	protected resultsFiltered_notsoftware(
		results_in: JSONArray<DataciteItem>
	): JSONArray<DataciteItem>{
		return results_in.filter(x => {
			return x.attributes?.types?.resourceTypeGeneral !== "Software";
		});
	}

	/** Keeps DataCite results of type `Dataset`. */
	protected resultsFiltered_dataset(
		results_in: JSONArray<DataciteItem>
	): JSONArray<DataciteItem>{
		return results_in.filter(x => {
			return x.attributes?.types?.resourceTypeGeneral === "Dataset";
		});
	}


	/** Removes DataCite results of type `Dataset`. */
	protected resultsFiltered_notdataset(
		results_in: JSONArray<DataciteItem>
	): JSONArray<DataciteItem>{
		return results_in.filter(x => {
			return x.attributes?.types?.resourceTypeGeneral !== "Dataset";
		});
	}

	/**
	 * Removes DataCite results that are a version of another record
	 * (`IsVersionOf`), keeping concept records.
	 */
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

	/**
	 * Sets the field a selected result is written to; by default also searches
	 * the parent field's current value. Returns the popup.
	 */
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

	/**
	 * Puts the query in the input and searches it if non-empty. Returns the
	 * popup.
	 */
	public withQuery(query: string): ApiQueryPopup {
		this.queryInputElement.value = query;
		if(query) this.submitQuery(query);
		return this;
	}

	/**
	 * Adds result filters by name (e.g. `software`, `concept`). Returns the
	 * popup.
	 */
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