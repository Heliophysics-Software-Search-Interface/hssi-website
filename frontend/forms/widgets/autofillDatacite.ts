import { 
    DataciteDoiWidget, faMagicIcon,
    FormGenerator,
    type DataciteItem, type JSONArray, type JSONObject,
} from "../../loader"

const orcidUrlPrefix = "https://orcid.org/";

export class AutofillDataciteWidget extends DataciteDoiWidget {

    protected autofillButton: HTMLButtonElement = null;
    
    private handleAutofill(): void {
        const data = this.parentField.getInputElement().data as DataciteItem;
        if(!data) return;
        console.log(data);

        const formData = {} as JSONObject;

        if(data.attributes){
            const attrs = data.attributes;

            // PID
            formData.persistentIdentifier = attrs.url;

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
                    else formData.description = desc_text;
                    if(formData.description && formData.conciseDescription){
                        break;
                    }
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
                            affiliation.affiliation = affil
                            affiliations.push(affiliation);
                        }
                        author.affiliation = affiliations;
                    }

                    // author identifier
                    if(creator.nameIdentifiers){
                        for(const nameId of creator.nameIdentifiers as JSONObject[]){
                            if(nameId.nameIdentifierScheme === "ORCID"){
                                author.identifier = orcidUrlPrefix + nameId.nameIdentifier;
                                break;
                            }
                        }
                    }

                    authors.push(author);
                }
                formData.authors = authors;
            }
        }

        console.log(formData);
        FormGenerator.fillForm(formData);
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
}