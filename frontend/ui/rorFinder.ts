import { 
	ApiQueryPopup, 
	type JSONArray, type JSONObject, type JSONValue 
} from "../loader";

export type RorItem = JSONObject & {
	id: string;
	names: RorName[];
};
type RorName = JSONObject & {
	lang: RorLang;
	types: RorType[];
	value: string;
};
type RorLang = "en" | "es" | "ar";
type RorType = "ror_display" | "label" | "acronym";

type RorSortedNames = {
	displayName: RorName;
	acronym: RorName;
	labels: RorName[];
}

/** 
 * extract which name is the display name, which is the acronymn, 
 * and which are just labels 
 */
function sortNames(names: RorName[]): RorSortedNames {
	const sortedNames: RorSortedNames = {
		displayName: null,
		acronym: null,
		labels: []
	};

	// loop allows us to prioritize english names first
	let onlyEnglish = true;
	while(true){

		// try to sort names into relevant categories
		for(const name of names) {
			if(onlyEnglish && name.lang !== "en") continue;
			if(name.types.includes("ror_display")) {
				sortedNames.displayName = name;
			}
			else if(name.types.includes("acronym")) {
				sortedNames.acronym = name;
			}
			else if(name.types.includes("label")) {
				sortedNames.labels.push(name);
				if(!sortedNames.displayName) sortedNames.displayName = name;
			}
		}

		// only try other languages if english is not available
		if (!onlyEnglish) break;
		else {
			if (!sortedNames.displayName) onlyEnglish = false;
			else break;
		}
	}
	return sortedNames;
}

/** interactive popup that allows a user to search for ROR ids by name */
export class RorFinder extends ApiQueryPopup {

	public override get title(): string {
		return "ROR Finder";
	}

	protected override get endpoint(): string {
		return "https://api.ror.org/v2/organizations";
	}

	protected override getQueryUrl(query: string): string {
		return this.endpoint + `?query=${query}`;
	}

	protected override getRequestHeaders(): Record<string, string> {
		const headers = super.getRequestHeaders();
		// TODO implement auth token without exposing it to frontend
		// (should probably implement a backend api endpoint for orcid searches)
		// headers["Authorization"] = `Bearer ${0}`;
		return headers;
	}

	protected override handleQueryResults(results: JSONValue): void {
		const data: any = results as any;
		if(data.items){
			const items = data.items as JSONObject[];
			for(const obj of items) {
				const item = obj as RorItem;
				const names = sortNames(item.names);
				
				// skip items without any name
				if(!names.displayName) continue;

				const content = document.createElement("div") as HTMLDivElement;
				content.innerText = names.displayName.value;
				if(names.acronym){
					content.innerText += ` (${names.acronym.value})`;
				}
				this.addResultRow({ 
					id: item.id, 
					textContent: content,
					jsonData: obj,
				});
			}
		}
	}

	/// Static -----------------------------------------------------------------

	private static instance: RorFinder = null;

	public static getInstance(): RorFinder {
		if (this.instance == null) this.instance = new RorFinder();
		return this.instance;
	}
}

(window as any).RorFinder = RorFinder;