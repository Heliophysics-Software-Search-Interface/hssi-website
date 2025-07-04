import { 
	DataciteDoiWidget, extractDoi, faMagicIcon,
	fetchTimeout,
	FormGenerator,
	Spinner,
	type DataciteItem, type JSONArray, type JSONObject,
} from "../../loader"

const orcidUrlPrefix = "https://orcid.org/";
const dataciteEntryApiEndpoint = "https://api.datacite.org/dois/";

export class AutofillDataciteWidget extends DataciteDoiWidget {

	protected autofillButton: HTMLButtonElement = null;
	
	private async getApiData(): Promise<DataciteItem> {

		const inputElem = this.parentField.getInputElement();
		let data = inputElem.data as DataciteItem;

		const doi = extractDoi(inputElem.value.trim());
		const dataDoi = data?.attributes?.doi;

		// if data was not stored in field (through find button), we need to
		// query the datacite api
		if(doi && doi != dataDoi) {
			try{ data = await AutofillDataciteWidget.getApiDataFromDoi(doi); }
			catch(e) { console.error(e); }
		}
		if(!data?.attributes) { 
			Spinner.hideSpinner(); 
			console.error("Error parsing datacite api data", data);
			return null;
		}

		return data;
	}

	private async handleAutofill(): Promise<void> {
		Spinner.showSpinner();

		const data = await this.getApiData();

		// parse the datacite api data
		try { AutofillDataciteWidget.autofillFromApiData(data); }
		catch(e){ console.error(e); }

		Spinner.hideSpinner();
	}

	private buildAutofillButton(): void {
		this.autofillButton = document.createElement("button");
		this.autofillButton.type = "button";
		this.autofillButton.innerHTML = faMagicIcon + " autofill";
		this.autofillButton.addEventListener(
			"click", () => this.handleAutofill()
		);

		this.element.appendChild(this.autofillButton);
	}

	override initialize(): void {
		super.initialize();
		this.buildAutofillButton();
	}

	/// Static -----------------------------------------------------------------

	public static async getApiDataFromDoi(doiUrl: string): Promise<DataciteItem> {
		
		const doi = extractDoi(doiUrl);
		
		console.log("Looking up datacite entry...", doi);
		const queryUrl = dataciteEntryApiEndpoint + doi;
		
		let data: DataciteItem = (
			await (await fetchTimeout(queryUrl)).json()
		).data as DataciteItem;

		return data;
	}

	public static autofillFromApiData(data: DataciteItem): void {

		console.log("Parsing datacite api data", data);
		const formData = {} as JSONObject;
		const attrs = data.attributes;

		// PID
		formData.persistentIdentifier = attrs.url;

		// publisher
		formData.publisher = attrs.publisher;

		// software name
		if(data.attributes.titles){
				for(const title of attrs.titles as JSONObject[]){
					formData.softwareName = title.title;
					break;
				}
		}
		
		// description
		if(attrs.descriptions){
				for(const desc of attrs.descriptions as JSONObject[]){
					const desc_text = desc.description as string;
					if(desc_text.length <= 200) {
						formData.conciseDescription = desc_text;
						if(!formData.description) {
							formData.description = desc_text
						}
					}
					else if(!formData.description) {
						formData.description = desc_text;
					}
					if (formData.descriptionType === "Abstract"){
						formData.description = desc_text;
					}
				}
				if(!formData.conciseDescription && formData.description){
					formData.conciseDescription = (
						formData.description as string
					).substring(0, 200);
				}
		}

		// authors
		if(attrs.creators){
				const authors: JSONArray<JSONObject> = [];
				for(const creator of attrs.creators as JSONObject[]) {
					const author = {} as JSONObject;
					
					// author name
					let name = "";
					if(creator.familyName && creator.givenName){
						name = (
							(creator.givenName as string).trim() + " " + 
							(creator.familyName as string).trim()
						);
					}
					else if(name.includes(',')){
						name = (name
							.split(',')
							.reverse()
							.map(x => x.trim())
							.filter(x => !!x)
							.join(' ')
						);
					}
					else name = (creator.name as string).trim();
					author.authors = name;

					// author affilitaions
					if(creator.affiliation){
						const affiliations = [] as JSONArray;
						for(const affil of creator.affiliation as string[]){
							const affiliation = {} as JSONObject;
							affiliation.authorAffiliation = affil;
							affiliations.push(affiliation);
						}
						author.authorAffiliation = affiliations;
					}

					// author identifier
					if(creator.nameIdentifiers){
						for(const nameId of creator.nameIdentifiers as JSONObject[]){
							if(nameId.nameIdentifierScheme === "ORCID"){
								author.authorIdentifier = (
									orcidUrlPrefix + nameId.nameIdentifier
								);
								break;
							}
						}
					}

					authors.push(author);
				}
				formData.authors = authors;
		}

		// license
		if(attrs.rightsList){
				for(const rights of attrs.rightsList as JSONObject[]){
					formData.license = rights.rights || rights.rightsIdentifier;
					if(formData.license) break;
				}
		}
		
		// awards
		const funders = [] as {funder?: string, funderIdentifier?: string}[];
		if(attrs.fundingReferences) {
				const awards = [] as JSONArray<JSONObject>;
				for(const fundRef of attrs.fundingReferences as JSONObject[]){
					const award = {} as JSONObject;
					award.awardTitle = fundRef.awardTitle;
					award.awardNumber = fundRef.awardNumber;
					if(fundRef.funderIdentifier || fundRef.funderName){
						funders.push({
							funder: fundRef.funderName as string,
							funderIdentifier: fundRef.funderIdentifier as string,
						});
					}
					awards.push(award);
				}
				formData.awardTitle = awards;
		}

		// funders
		if(funders){
				for(const funder of funders){
					// TODO multifield
					formData.funder = funder;
					break; 
				}
		}

		// publication date
		if(attrs.dates){
			const pubdate = attrs.dates.find(item => item.dateType === "Issued");
			if (pubdate){
				formData.publicationDate = pubdate.date;
			}
		}

		// documentation, ref publication, rel publications
		const relPubs: string[] = [];
		if(attrs.relatedIdentifiers){
			for(const relId of attrs.relatedIdentifiers){
				// docs
				if(relId.relationType === "IsDocumentedBy"){
					formData.documentation = relId.relatedIdentifier;
					if(formData.documentation) break;
				}

				// ref pub
				if(relId.resourceTypeGeneral === "JournalArticle"){
					if(
						!formData.referencePublication && 
						relId.relationType === "IsDescribedBy"
					) formData.referencePublication = relId.relatedIdentifier;
					else{
						relPubs.push(relId.relatedIdentifier);
					}
				}
			}
		}
		if(relPubs) formData.relatedPublications = relPubs;

		// version
		if(attrs.version){
			formData.versionNumber = {
				versionNumber: attrs.version,
				versionDate: attrs.updated?.split('T')[0],
			};
		}

		// keywords
		if(attrs.subjects){
			formData.keywords = [];
			for(const item of attrs.subjects as {subject: string}[]){
				// capitalize first char and skip empty/whitespace strings
				let subject = item.subject;
				subject = subject.trim();
				if(subject.length <= 0) continue;
				subject = subject[0].toLocaleUpperCase() + subject.slice(1);
				formData.keywords.push(subject);
			}
		}

		console.log(formData);
		FormGenerator.fillForm(formData);
	}
}