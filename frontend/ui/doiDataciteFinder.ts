import { 
	ApiQueryPopup,
	type ApiQueryResult, type JSONArray, type JSONObject, type JSONValue 
} from "../loader";

export type ZenodoApiItem = {
	created: string,
	modified: string,
	id: number,
	conceptrecid: string,
	doi: string,
	conceptdoi: string,
	doi_url: string,
	metadata: JSONObject & {
		custom: JSONObject & {
			"code:codeRepository": string,
			"code:programmingLanguage": {
				id: string,
				title: JSONObject & {
					en: string,
				},
			}[],
			"code:developmentStatus": {
				id: string,
				title: JSONObject & {
					en: string,
				},
			}
		}
	},
	title: string,
	links: JSONObject,
	updated: string,
	recid: string,
	revision: number,
	files: JSONArray,
	swh: JSONObject,
	owners: JSONArray,
	status: string,
	stats: JSONObject,
	state: string,
	submitted: boolean,
}

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
	dates: JSONArray<JSONObject & {
		date: string,
		dateType: string,
	}>,
	subjects: JSONArray,
	contributors: JSONArray,
	language: string | null,
	types: JSONObject & { 
		resourceType: String,
		resourceTypeGeneral: string,
	},
	relatedIdentifiers: JSONArray< JSONObject & {
		relatedIdentifier?: string,
		relatedIdentifierType?: string & (
			"URL" |
			"DOI" 
		),
		resourceTypeGeneral?: string & (
			"Software" |
			"JournalArticle"
		),
		relationType: string & (
			"IsDescribedBy" |
			"IsNewVersionOf" |
			"IsVersionOf" |
			"HasVersion" |
			"HasMetadata" |
			"IsDocumentedBy" |
			"IsDerivedFrom" 
		),
	}>,
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

	protected override get description(): string { return (
		"Enter the name or keywords of an item to find it's DOI."
	); };

	public override get title(): string { return "Datacite Search"; }

	protected override get endpoint(): string {
		return "https://api.datacite.org/dois";
	}

	protected override getQueryUrl(query: string): string {
		const formattedQuery = query.trim().split(/\s+/).join("+");
		return this.endpoint + `?query=${formattedQuery}`;
	}

	protected override handleQueryResults(results: JSONValue): void {
		
		// get filtered results
		let items = (results as JSONObject).data as DataciteItem[];
		if(this.filters) {
			if(items.length > 250) items.splice(250);
			items = this.filterResults(items) as any;
		}

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