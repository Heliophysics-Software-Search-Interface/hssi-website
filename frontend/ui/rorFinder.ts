import { ApiQueryPopup, type JSONArray, type JSONObject, type JSONValue } from "../loader";

type RorItem = JSONObject & {
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
    for(const name of names) {
        if(name.lang !== "en") continue;
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
    return sortedNames;
}

/** interactive popup that allows a user to search for ROR ids by name */
export class RorFinder extends ApiQueryPopup {

    override get title(): string {
        return "ROR Finder";
    }

    protected override get endpoint(): string {
        return "https://api.ror.org/v2/organizations";
    }

    protected override async getQueryResults(query: string): Promise<JSONValue> {
        const queryUrl = this.endpoint + `?query=${query}`;
        const response = await fetch(queryUrl, { method: "GET" });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(`Error fetching data: ${response.status} ${response.statusText}`);
        }
        return data;
    }

    protected override handleQueryResults(results: JSONValue): void {
        const data: any = results as any;
        if(data.items){
            const items = data.items as JSONArray;
            for(const obj of items) {
                console.log(obj);
                const item = obj as RorItem;
                const names = sortNames(item.names);
                const content = document.createElement("div") as HTMLDivElement;
                content.innerText = names.displayName.value;
                if(names.acronym){
                    content.innerText += ` (${names.acronym.value})`;
                }
                this.addResultRow({ id: item.id, textContent: content });
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