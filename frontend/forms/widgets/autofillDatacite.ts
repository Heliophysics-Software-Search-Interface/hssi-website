import {
	ConfirmDialogue,
	DataciteDoiWidget, extractDoi, faMagicIcon, fetchTimeout, FormGenerator,
	PopupDialogue,
	Spinner,
	type DataciteItem, type JSONArray, type JSONObject, type SubmissionFormData,
	type ZenodoApiItem,
} from "../../loader"

const orcidUrlPrefix = "https://orcid.org/";
const doiUrlPrefix = "https://doi.org/";
const zenodoApiPrefix = "https://zenodo.org/api/records/";
const rorUrlPrefix = "https://ror.org/";
const dataciteEntryApiEndpoint = "https://api.datacite.org/dois/";

const resTypeGensPublication = [
	"journalarticle",
	"bookchapter",
	"conferencepaper",
	"conferenceproceeding",
	"datapaper",
	"dissertation",
	"peerreview",
	"preprint",
	"scholarlyarticle",
	"studyregistration",
];
const resTypeGensSoftware = [
	"softwaresourcecode",
	"softwareapplication",
	"software",
];
const resTypeGensDataset = [
	"dataset",
]

// TODO implement proper json-ld parsing through:
// https://github.com/digitalbazaar/jsonld.js/tree/main

export class AutofillDataciteWidget extends DataciteDoiWidget {

	protected autofillButton: HTMLButtonElement = null;
	
	private getDoi(): string {
		const inputElem = this.parentField.getInputElement();
		let data = inputElem.data as DataciteItem;

		const doi = extractDoi(inputElem.value.trim());
		const dataDoi = data?.attributes?.doi;

		return doi || dataDoi;
	}

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
		const zenodoData = await AutofillDataciteWidget.getZenodoApiDataFromDoi(
			this.getDoi()
		);

		// parse the datacite api data
		try { AutofillDataciteWidget.autofillFromApiData(data, zenodoData); }
		catch(e){ console.error(e); }

		Spinner.hideSpinner();
	}

	override initialize(): void {
		super.initialize();
		this.parentField?.requirement?.containerElement?.addEventListener(
			"focusout", async e => {
				if(!FormGenerator.markAutofilledDatacite && this.parentField.hasValidInput()){
					if(await ConfirmDialogue.getConfirmation(
						"It looks like the identifier you entered can be " +
						"used to fetch relevant data about your software " + 
						"from datacite. Would you like to use this data " +
						"to autofill the form? If so, please ensure "+ 
						"autofilled information is accurate.", 
						"Autofill Prompt"
					)) this.handleAutofill();
				}
		});
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

	public static async getZenodoApiDataFromDoi(
		doiUrl: string
	): Promise<ZenodoApiItem> {
		const zenodoRecord = doiUrl.toLowerCase().split("zenodo.").at(-1);
		const zenodoApiUrl = zenodoApiPrefix + zenodoRecord;
		const zenodoData: ZenodoApiItem = await (await fetchTimeout(zenodoApiUrl)).json();
		return zenodoData;
	}

	public static autofillFromApiData(
		data: DataciteItem, 
		zenodoData: ZenodoApiItem = {} as any,
	): void {
		FormGenerator.markAutofilledDatacite();

		console.log("Parsing datacite api data", data);
		const formData = {} as SubmissionFormData;
		const attrs = data.attributes;

		if(!zenodoData) zenodoData = {} as any;

		// PID
		const doi = zenodoData.conceptdoi || data.id;
		formData.persistentIdentifier = doiUrlPrefix + doi;

		// publisher
		formData.publisher = {
			publisher: attrs.publisher,
		}

		// software name
		if(data.attributes.titles){
				for(const title of attrs.titles as JSONObject[]){
					formData.softwareName = title.title as string;
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
					if (desc.descriptionType === "Abstract"){
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
					formData.license = {
						license: (rights.rights || rights.rightsIdentifier) as string,
						licenseURI: (rights.rightsUri || rights.schemeUri) as string,
					}
					if(formData.license) break;
				}
		}
		
		// awards, funders
		const funders = [] as {funder?: string, funderIdentifier?: string}[];
		if(attrs.fundingReferences) {
				const awards = [] as JSONArray<JSONObject>;
				for(const fundRef of attrs.fundingReferences as JSONObject[]){
					const award = {} as JSONObject;
					award.awardTitle = fundRef.awardTitle;
					award.awardNumber = fundRef.awardNumber;
					if(fundRef.funderIdentifier || fundRef.funderName){
						// crossref doi (not a ror)
						const funderId = (
							doiUrlPrefix + fundRef.funderIdentifier as string
						);

						// ensure no duplicate funders
						let addFunder = true;
						for(const prevFunder of funders){
							if(
								prevFunder.funderIdentifier == funderId || 
								prevFunder.funder == fundRef.funderName
							){
								addFunder = false;
								break;
							}
						}
						if(addFunder) funders.push({
							funder: fundRef.funderName as string,
							// fund id is invalid - datacite uses crossref ids 
							// for organizations instead of rors
							// funderIdentifier: funderId, 
						});
					}
					awards.push(award);
				}
				formData.awardTitle = awards;
		}

		// funders
		if(funders) formData.funder = funders;

		// publication date
		if(attrs.dates){
			const pubdate = attrs.dates.find(item => item.dateType === "Issued");
			if (pubdate){
				formData.publicationDate = pubdate.date;
			}
		}

		// documentation, code repo url, ref publication, rel publications, 
		// rel software, rel datasets
		const relPubs: string[] = [];
		const relSoftware: string[] = [];
		const relData: string[] = [];
		if(attrs.relatedIdentifiers){
			for(const relId of attrs.relatedIdentifiers){
				// docs
				if(relId.relationType === "IsDocumentedBy"){
					if(!formData.documentation){
						formData.documentation = relId.relatedIdentifier;
					}
				}

				// code repository url
				else if(relId.relationType === "IsDerivedFrom") {
					if(relId.relatedIdentifierType === "URL"){
						formData.codeRepositoryURL = relId.relatedIdentifier;
					}
				}

				// reference/related publication
				const resTypeGen = relId.resourceTypeGeneral?.toLocaleLowerCase();
				if(resTypeGen){
					if(resTypeGen in resTypeGensPublication){
						if(
							!formData.referencePublication && 
							relId.relationType === "IsDescribedBy"
						) formData.referencePublication = relId.relatedIdentifier;
						else{
							relPubs.push(relId.relatedIdentifier);
						}
					}

					// related datasets
					else if(resTypeGen in resTypeGensDataset){
						relData.push(relId.relatedIdentifier);
					}

					// related software
					else if(resTypeGen in resTypeGensSoftware){
						relSoftware.push(relId.relatedIdentifier);
					}
				}
			}
		}

		// code repo url try #2 (zenodo)
		const repoUrl = zenodoData?.metadata?.custom?.["code:codeRepository"];
		if(repoUrl) formData.codeRepositoryURL = repoUrl;

		// set the related identifiers
		if(relPubs) formData.relatedPublications = relPubs.map(doi => doiUrlPrefix + doi);
		if(relSoftware) formData.relatedSoftware = relSoftware.map(doi => doiUrlPrefix + doi);
		if(relData) formData.relatedDatasets = relData.map(doi => doiUrlPrefix + doi);

		// version
		if(attrs.version){
			formData.versionNumber = {
				versionNumber: attrs.version,
				versionDate: attrs.updated?.split('T')[0],
				// innaccurate - gives concept doi, and we cannot find newest 
				// version doi without multiple api queries
				// versionPID: doiUrlPrefix + data.id, 
			};
			const desc = formData.description || formData.conciseDescription;
			if(desc) {
				formData.versionNumber.versionDescription = desc
			}
			if(zenodoData?.doi){
				formData.versionNumber.versionPID = doiUrlPrefix + zenodoData.doi;
			}
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

		// repo status
		console.log(zenodoData);
		const devStatus = zenodoData?.metadata?.custom?.["code:developmentStatus"];
		if(devStatus){
			formData.developmentStatus = devStatus.title?.en || devStatus.id;
		}

		// programming languages
		const progLangs = zenodoData?.metadata?.custom?.["code:programmingLanguage"];
		if(progLangs){
			formData.programmingLanguage = [];
			for(const lang of progLangs){
				const langName = lang.title?.en || lang.id;
				formData.programmingLanguage.push(langName);
			}
		}

		console.log(formData);
		FormGenerator.fillForm(formData);
	}
}