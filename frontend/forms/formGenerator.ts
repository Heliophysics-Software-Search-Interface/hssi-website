import { 
    typeAttribute, ModelFieldStructure, ModelSubfield, widgetDataAttribute
} from "../loader";

const generatedFormType = "generated-form";
const formFieldsType = "form-field-container";
const structureNameData = "fields-structure-name";

const modelStructureUrl = "/api/model_structure/";


type ModelStructureData = {
    structures: ModelFieldStructure[],
}

export class FormGenerator {
    
    private formElement: HTMLFormElement = null;
    private fieldContainer: HTMLDivElement = null;
    private fields: ModelSubfield[] = [];

    private buildForm(): void {

        // don't try to generate the form without structure data
        if(FormGenerator.structureData == null) {
            throw new Error(
                "Form cannot generate without model structure data"
            );
        }

        // generate a row for each field
        for(const field of this.fields) {
            const formRow = document.createElement("div") as HTMLDivElement;
            field.buildInterface(formRow);
            this.fieldContainer.appendChild(formRow);
        }
    }

    private static formGenerator: FormGenerator = null;
    private static structureData: ModelStructureData = null;

    /** 
     * generate a form from a given set of fields, or if not specified, tries 
     * to find json data about fields inside the text
     */
    public static generateForm(fields: ModelSubfield[] = null): void {

        // warn about singleton resetting
        if(this.formGenerator != null) {
            console.warn("form generator running multiple times on same page");
        }

        // if there is no form, return early
        const form = document.querySelector(
            `form[${typeAttribute}=${generatedFormType}]`
        ) as HTMLFormElement;
        if(form == null) return;

        // otherwise get references to or create the form elements
        const generator = new FormGenerator();
        generator.formElement = form;
        generator.fieldContainer = generator.formElement.querySelector(
            `div[${typeAttribute}=${formFieldsType}]`
        );
        if (generator.fieldContainer == null) {
            generator.fieldContainer = document.createElement("div");
            generator.fieldContainer.setAttribute(typeAttribute, formFieldsType);
            generator.formElement.appendChild(generator.fieldContainer);
        }
        
        // get fields from html elements if not specified in function
        if(fields == null) {
            const dataElement: HTMLScriptElement = 
                generator.formElement.querySelector(
                    `script[${widgetDataAttribute}=${structureNameData}]`
                );
            if(dataElement) {
                const structure = ModelFieldStructure.getFieldStructure(
                    dataElement.textContent.trim()
                ).generateInstance();
                const fields = [structure.topField, ...structure.subFields];
                generator.fields = fields;
            }
        }
        else generator.fields = fields;

        // apply the singleton instance
        this.formGenerator = generator;
        
        // generate the form if structure data is already loaded
        if(FormGenerator.structureData != null) { 
            this.formGenerator.buildForm();
        }

        // otherwise get the structure data and then generate the form
        else {
            const request = fetch(modelStructureUrl);
            request.then(response => response.json()).then(data => {
                const structureData = data as ModelStructureData;
                FormGenerator.structureData = structureData;
                FormGenerator.formGenerator.buildForm();
            }).catch(error => {
                console.error(error);
            });
        }
    }
}