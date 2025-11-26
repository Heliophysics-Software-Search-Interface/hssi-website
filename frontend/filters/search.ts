import { 
	type SoftwareDataAsync,
	ApiQueryPopup,
	ConfirmDialogue,
	ModelDataCache, 
	PopupDialogue, 
	ResourceView,
	Spinner, 
} from "../loader";

export const idSearchbar = "searchbar";
export const idSearchButton = "searchbar-btn";
export const searchParamQuery = "q";

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
	if (searchVal) searchForQuery(searchVal, false);

	const searchbar = document.getElementById(idSearchbar) as HTMLInputElement;
	if(searchbar) searchbar.value = searchVal;
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

export async function searchForQuery(
	query: string, 
	pushHistory: boolean = true
): Promise<void> {

	Spinner.showSpinner(`Searching for '${query}'`);

	try{
		// get all search results relevant to the query
		const relevantSoftwareIds = await getReleventQueryResults(query);
		
		// refresh the items in the resource view to only display search results
		const view = ResourceView.main;
		view.filterToItems(relevantSoftwareIds);
		view.refreshItems();
		
		if (pushHistory) recordHistory(query);
		
		console.log(`queried '${query}', results:`, relevantSoftwareIds);	

		setTimeout(() => {
			Spinner.hideSpinner();
		}, 100);
		updateTitleToSearch();
	}
	catch(e) {
		Spinner.hideSpinner();
		ConfirmDialogue.getConfirmation(e?.toString() || "", "Error", "Ok", null);
	}
}

export async function getReleventQueryResults(query: string): Promise<string[]> {
	const datas = await ModelDataCache.getModelDataAll("Software");

	// get all search results relevant to the query
	const titleRelevant: SoftwareDataAsync[] = [];
	const descriptionRelevant: SoftwareDataAsync[] = [];
	const otherRelevant: SoftwareDataAsync[] = [];
	const splitQuery = query.toLowerCase().split(/\s+/);
	for(const data of datas){
		for(const term of splitQuery){
			if(data.softwareName.toLowerCase().includes(term)) {
				titleRelevant.push(data);
			}
			else if (
				data.conciseDescription.toLowerCase().includes(term) || 
				data.description.includes(term)
			){
				descriptionRelevant.push(data);
			}
			else if (data.codeRepositoryUrl.toLowerCase().includes(term)){
				otherRelevant.push(data);
			}
			else if (data.persistentIdentifier.toLowerCase().includes(term)){
				otherRelevant.push(data);
			}
			else if (data.id.toLowerCase().includes(term)) {
				otherRelevant.push(data);
			}
		}
	}
	const relevantSoftwareIds = (
		titleRelevant.map(s => s.id)
			.concat(descriptionRelevant.map(s => s.id))
			.concat(otherRelevant.map(s => s.id))
	)

	// TODO sort by relevance score

	return relevantSoftwareIds;
}

window.addEventListener("load", initializeSearch);