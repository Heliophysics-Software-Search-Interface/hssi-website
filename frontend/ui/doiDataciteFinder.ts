import { 
    ApiQueryPopup, 
    type ApiQueryResult, type JSONArray, type JSONObject, type JSONValue 
} from "../loader";

type DataciteItem = {
    id: string,
    type: string,
    attributes: DataciteAttributes,
    relationships: JSONObject,
}

type DataciteAttributes = JSONObject & {
    doi: string,
    identifiers: JSONArray,
    creators: JSONArray,
    titles: JSONObject[],
    publisher: string,
    container: JSONObject,
    publicationYear: Number,
    subjects: JSONArray,
    contributors: JSONArray,
    language: string | null,
    types: JSONObject,
    relatedIdentifiers: JSONArray,
    relatedItems: JSONArray,
    rightsList: JSONArray,
    descriptions: JSONArray,
    fundingReferences: JSONArray,
    url: string,
    isActive: boolean,
    created: string,
    registered: string,
    published: string | null,
    updated: string,
}

export class DoiDataciteFinder extends ApiQueryPopup {

    public override get title(): string { return "Datacite Search"; }

    protected override get endpoint(): string {
        return "https://api.datacite.org/dois";
    }

    protected override getQueryUrl(query: string): string {
        const formattedQuery = query.trim().split(/\s+/).join("+");
        return this.endpoint + `?query=${formattedQuery}`;
    }

    protected override handleQueryResults(results: JSONValue): void {
        const items = (results as JSONObject).data as DataciteItem[];
        for(const item of items) {
            const content = document.createElement("div");
            const title = (item.attributes.titles[0]["title"] ?? "Unknown").toString();
            content.innerText = title;
            if(item.attributes.publicationYear) {
                content.innerText += ` (${item.attributes.publicationYear})`;
            }
            const result: ApiQueryResult = {
                id: `https://doi.org/${item.id}`,
                textContent: content,
            }
            this.addResultRow(result);
        }
    }

    /// Static -----------------------------------------------------------------

    private static instance: DoiDataciteFinder = null;

    public static getInstance(): DoiDataciteFinder {
        if (this.instance == null) this.instance = new DoiDataciteFinder();
        return this.instance;
    }
}

(window as any).DoiDataciteFinder = DoiDataciteFinder;