import { 
	ApiQueryPopup, 
	type ApiQueryResult, type JSONObject, type JSONValue 
} from "../loader";

const queryMaxRows = 50;

export type OrcidItem = {
	email: string[],
	"family-names": string,
	"given-names": string,
	"institution-name": string[],
	"orcid-id": string,
	"other-name": string[],
}

export class OrcidFinder extends ApiQueryPopup {
	
	public override get title(): string { return "ORCID Finder"; }

	protected override get endpoint(): string {
		return "https://pub.orcid.org/v3.0/expanded-search/";
	}
	
	protected override get contentType(): string {
		return "application/vnd.orcid+json";
	}

	protected override getQueryUrl(query: string): string {
		const formattedQuery = query.trim().split(/\s+/).join("+AND+");
		return this.endpoint + `?q=${formattedQuery}&rows=${queryMaxRows}`;
	}

	protected override handleQueryResults(results: JSONValue): void {
		const items = (results as JSONObject)["expanded-result"] as OrcidItem[];
		if(items == null) return;

		for(const item of items) {
			const name = document.createElement("span");
			name.style.fontWeight = "bold";
			const divider = document.createElement("span");
			const orgs = document.createElement("span");
			orgs.style.fontStyle = "italic";
			
			name.innerText = `${item["given-names"]} ${item["family-names"]}`;
			divider.innerText = " - ";

			const orgNames = item["institution-name"];
			orgNames.length = Math.min(orgNames.length, 5);
			orgs.innerText = orgNames.join(", ");

			const content = document.createElement("div");
			content.appendChild(name);
			if(orgNames.length > 0){
				content.appendChild(divider);
				content.appendChild(orgs);
			}
			const qResult: ApiQueryResult = {
				id: `https://orcid.org/${item["orcid-id"]}`,
				textContent: content,
				jsonData: item,
			}
			this.addResultRow(qResult);
		}
	}

	/// Static -----------------------------------------------------------------

	private static instance: OrcidFinder = null;

	public static getInstance(): OrcidFinder {
		if (this.instance == null) this.instance = new OrcidFinder();
		return this.instance;
	}
}

(window as any).OrcidFinder = OrcidFinder;