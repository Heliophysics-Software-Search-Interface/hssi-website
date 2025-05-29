import { 
    typeAttribute, ModelFieldStructure, ModelSubfield, widgetDataAttribute,
    type SerializedSubfield
} from "../loader";

const generatedFormType = "generated-form";
const formFieldsType = "form-field-container";
const structureNameData = "fields-structure-name";

const modelStructureUrl = "/api/model_structure/";

export const formRowStyle = "form-row";
export const formSeparatorStyle = "form-separator"

type ModelStructureData = {
    data: ModelFieldStructure[],
}

export class FormGenerator {

    private formElement: HTMLFormElement = null;
    private fieldContainer: HTMLDivElement = null;
    private fields: (ModelSubfield | ModelSubfield[])[] = [];

    private buildForm(): void {

        // don't try to generate the form without structure data
        if(FormGenerator.structureData == null) {
            throw new Error(
                "Form cannot generate without model structure data"
            );
        }

        // generate a row for each field
        let i = 0;
        const titles: string[] = [
            "",
            "Additional Data (click to expand)",
            "Additional Metadata (click to expand)",
            "",
        ];
        for(const field of this.fields) {
            if(field instanceof Array){
                this.buildFormSection(field, titles.shift(), i > 0 && i < this.fields.length - 1);
                i++;
                continue;
            }
            const formRow = document.createElement("div") as HTMLDivElement;
            formRow.classList.add(formRowStyle);
            field.buildInterface(formRow);
            this.fieldContainer.appendChild(formRow);
            i++;
        }
    }

    private buildFormSection(
        fields: ModelSubfield[], 
        title: string,
        collapsible: boolean = true,
    ): void {

        const details = document.createElement(collapsible ? "details" : "div");
        details.classList.add(formSeparatorStyle);
        const summary = document.createElement("summary");
        summary.innerText = title;
        details.appendChild(summary);

        for(const field of fields) {
            const formRow = document.createElement("div") as HTMLDivElement;
            formRow.classList.add(formRowStyle);
            field.buildInterface(formRow);
            details.appendChild(formRow);
        }

        this.fieldContainer.appendChild(details);
    }

    private static formGenerator: FormGenerator = null;
    private static structureData: ModelStructureData = null;

    /** 
     * generate a form from a given set of fields, or if not specified, tries 
     * to find json data about fields inside the text
     */
    public static async generateForm(fields: ModelSubfield[] = null): Promise<void> {

        // warn about singleton resetting
        if(this.formGenerator != null) {
            console.warn("form generator running multiple times on same page");
        }

        // if there is no form, return early
        const form = document.querySelector(
            `form[${typeAttribute}=${generatedFormType}]`
        ) as HTMLFormElement;
        if(form == null) return;

        // TODO placeholder form loading icon

        // load structure data
        if(this.structureData == null) {
            const response = await fetch(modelStructureUrl);
            const data = await response.json();
            const structureData = data as ModelStructureData;
            this.structureData = structureData;
            ModelFieldStructure.parseBasicWidgetModels();
            ModelFieldStructure.parseModels(this.structureData.data);
        }

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
                document.querySelector(
                    `script[${widgetDataAttribute}=${structureNameData}]`
                );
            if(dataElement) {
                const content = JSON.parse(dataElement.textContent.trim());
                if(content instanceof Array){
                    const fieldSets: ModelSubfield[] = [];
                    for(const structureName of content){
                        const structure = ModelFieldStructure.getFieldStructure(structureName);
                        if(structure == null){
                            console.log(`structure is underfined for ${structureName}`);
                        }
                        const structInstance = structure.generateInstance();
                        fieldSets.push([
                            structInstance.topField, 
                            ...structInstance.subFields
                        ] as any);
                    }
                    generator.fields = fieldSets as any;
                }
                else{
                    const structure = ModelFieldStructure.getFieldStructure(content);
                    const fieldInstance = structure.generateInstance();
                    const fields = [fieldInstance.topField, ...fieldInstance.subFields];
                    generator.fields = fields;
                }
            }
            else console.warn("No field data found in form");
        }
        else generator.fields = fields;

        // apply the singleton instance
        this.formGenerator = generator;
        this.formGenerator.buildForm();
        
    }
}