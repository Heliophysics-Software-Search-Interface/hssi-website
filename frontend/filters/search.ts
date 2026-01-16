import { 
	type SoftwareDataAsync,
	ApiQueryPopup,
	ConfirmDialogue,
	ModelDataCache, 
	PopupDialogue, 
	ResourceView,
	Spinner, 
	fetchTimeout,
} from "../loader";

export const idSearchbar = "searchbar";
export const idSearchButton = "searchbar-btn";
export const searchParamQuery = "q";
const searchApiUrl = "/api/search/";

/** 
 * add event listeners to search bar / button and fill search bar with query 
 * if one is specified in url params. Other basic setup utility
 */
function initializeSearch(): void {
	const searchbar = document.getElementById(idSearchbar) as HTMLInputElement;
	const searchTerm = getSearchTerm();
	searchbar.value = searchTerm;
	searchbar.addEventListener("keydown", e => {
		if(e.key == "Enter") onEnterSearch();
	});

	const searchButton = document.getElementById(idSearchButton) as HTMLButtonElement;
	searchButton.addEventListener("click", onEnterSearch);

	window.addEventListener("popstate", _ => { parseUrlParams(); });

	parseUrlParams();
}

function updateTitleToSearch() {
	const searchTerm = getSearchTerm();
	if(searchTerm) document.title = `HSSI Search - '${searchTerm}'`;
	else document.title = document.title.split(' - ')[0]
}

/** search based on input into the search box */
function onEnterSearch(): void {
	const searchbar = document.getElementById(idSearchbar) as HTMLInputElement;
	const query = searchbar.value;

	searchForQuery(query);
}

function parseUrlParams() {
	const search = new URLSearchParams(window.location.search);
	const searchVal = search.get("q");
	if (searchVal) {
		searchForQuery(searchVal, false);
	} else {
		const view = ResourceView.main;
		if (view) view.showItems(view.getFilteredItems());
		updateTitleToSearch();
	}

	const searchbar = document.getElementById(idSearchbar) as HTMLInputElement;
	if(searchbar) searchbar.value = searchVal || "";
}

function recordHistory(query: string){

	// Record search to browser history
	const newUrl = new URL(window.location.href);
	if (query) newUrl.searchParams.set(searchParamQuery, query);
	else newUrl.searchParams.delete(searchParamQuery);
	history.pushState(null, "", newUrl);
}

/** 
 * gets the search term first from the search bar or from the query 
 * params if search bar is empty or does not exist
 */
function getSearchTerm(): string {
	const searchbar = document.getElementById(idSearchbar) as HTMLInputElement;
	if(searchbar?.value) return searchbar.value;

	const search = new URLSearchParams(window.location.search);
	const searchVal = search.get("q");
	return searchVal || "";
}

/**
 * applies the previously entered search to the main resource view
 * @param pushHistory whether or not this search is recorded in browser history
 */
export async function applyEnteredQuery(pushHistory: boolean = false){
	parseUrlParams();
}

export async function searchForQuery(
	query: string, 
	pushHistory: boolean = true
): Promise<void> {
	const trimmedQuery = query.trim();
	if (!trimmedQuery) {
		const view = ResourceView.main;
		if (view) view.showItems(view.getFilteredItems());
		if (pushHistory) recordHistory("");
		updateTitleToSearch();
		return;
	}

	Spinner.showSpinner(`Searching for '${trimmedQuery}'`);

	try{
		const resultIds = await getRelevantQueryIds(trimmedQuery);
		const resultData = await ModelDataCache.getModelData(
			"VisibleSoftware",
			resultIds
		) as SoftwareDataAsync[];

		const view = ResourceView.main;
		const filteredItems = view.getFilteredItems();
		const filteredIds = new Set(
			filteredItems.map(item => item.id.toLowerCase())
		);
		const dataMap = new Map(
			resultData.map(item => [item.id.toLowerCase(), item])
		);
		const filteredResults: SoftwareDataAsync[] = [];
		for(const id of resultIds){
			const item = dataMap.get(id.toLowerCase());
			if(item && filteredIds.has(item.id.toLowerCase())) {
				filteredResults.push(item);
			}
		}
		view.showItems(filteredResults);
		
		if (pushHistory) recordHistory(trimmedQuery);
		
		console.log(`queried '${trimmedQuery}', results:`, filteredResults);	

		setTimeout(() => { Spinner.hideSpinner(); }, 100);
		updateTitleToSearch();
	}
	catch(e) {
		Spinner.hideSpinner();
		ConfirmDialogue.getConfirmation(e?.toString() || "", "Error", "Ok", null);
	}
}

async function getRelevantQueryIds(query: string): Promise<string[]> {
	const url = new URL(searchApiUrl, window.location.origin);
	url.searchParams.set(searchParamQuery, query);
	const response = await fetchTimeout(url.toString());
	if (!response.ok) {
		throw new Error(`Search request failed with ${response.status}`);
	}
	const data = await response.json();
	if (!data?.results) return [];
	return data.results as string[];
}

window.addEventListener("load", initializeSearch);
