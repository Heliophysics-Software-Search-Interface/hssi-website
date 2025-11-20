import { 
	type SoftwareDataAsync,
	ModelDataCache, 
	ResourceView, 
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
	searchbar.value = getSearchTerm();
	searchbar.addEventListener("keydown", e => {
		if(e.key == "Enter") onEnterSearch();
	});

	const searchButton = document.getElementById(idSearchButton) as HTMLButtonElement;
	searchButton.addEventListener("click", onEnterSearch);
}

/** search based on input into the search box */
function onEnterSearch(): void {
	const searchbar = document.getElementById(idSearchbar) as HTMLInputElement;
	const query = searchbar.value
	searchForQuery(query);
}

/** 
 * gets the search term first from the search bar or from the query 
 * params if search bar is empty or does not exist
 */
export function getSearchTerm(): string {
	const searchbar = document.getElementById(idSearchbar) as HTMLInputElement;
	if(searchbar?.value) return searchbar.value;

	const search = new URLSearchParams(window.location.search);
	const searchVal = search.get("q");
	return searchVal || "";
}

export function searchForQuery(query: string): void {
	const promise = ModelDataCache.getModelDataAll("Software")
	promise.then(datas => {

		// get all search results relevant to the query
		const titleRelevant: SoftwareDataAsync[] = [];
		const descriptionRelevant: SoftwareDataAsync[] = [];
		const otherRelevant: SoftwareDataAsync[] = [];
		const splitQuery = query.toLowerCase().split(/\s+/);
		for(const data of datas){
			for(const term of splitQuery){
				if(data.softwareName.includes(term)) {
					titleRelevant.push(data);
				}
				else if (
					data.conciseDescription.includes(term) || 
					data.description.includes(term)
				){
					descriptionRelevant.push(data);
				}
				else if (data.codeRepositoryUrl.includes(term)){
					otherRelevant.push(data);
				}
				else if (data.persistentIdentifier.includes(term)){
					otherRelevant.push(data);
				}
				else if (data.id.includes(term)) {
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
		
		// refresh the items in the resource view to only display search results
		const view = ResourceView.getMainView();
		view.filterToItems(relevantSoftwareIds);
		view.refreshItems();

		// Record search to browser history
		const newUrl = new URL(window.location.href);
		newUrl.searchParams.set(searchParamQuery, query);
		history.pushState(null, "", newUrl);

		console.log(`queried '${query}', results:`, relevantSoftwareIds);
	});
}

window.addEventListener("load", initializeSearch);