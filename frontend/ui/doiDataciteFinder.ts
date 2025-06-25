import { 
    ApiQueryPopup, 
    type ApiQueryResult, type JSONArray, type JSONObject, type JSONValue 
} from "../loader";

export type DataciteItem = {
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
    version: string,
    versionCount: number,
}

function isConceptDoi(attrs: DataciteAttributes): boolean {
    if(attrs.relatedIdentifiers){
        for(const rel of attrs.relatedIdentifiers as JSONObject[]){
            if(rel.relationType && rel.relationType === "HasVersion") {
                return true;
            }
        }
    }
    return false;
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
            const titleElem = document.createElement("div");
            titleElem.innerText = title;
            titleElem.style.fontWeight = "bold";

            const infoElem = document.createElement("div");
            infoElem.style.fontStyle = "italic";

            const texts: string[] = []
            if(item.attributes.types){
                const text = (
                    item.attributes.types.resourceType || 
                    item.attributes.types.resourceTypeGeneral
                ) as string;
                if(text) texts.push(text);
            }
            if(isConceptDoi(item.attributes)) {
                texts.push(`concept`);
            }
            else if (item.attributes.version) {
                texts.push(`${item.attributes.version}`.trim());
            }
            if(item.attributes.publicationYear) {
                texts.push(item.attributes.publicationYear.toString());
            }
            infoElem.innerText = texts.join(", ");

            content.appendChild(titleElem);
            content.appendChild(infoElem);
            const result: ApiQueryResult = {
                id: `https://doi.org/${item.id}`,
                textContent: content,
                jsonData: item,
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