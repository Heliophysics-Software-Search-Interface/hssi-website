/// In order to create infinite depth recursive dynamically generated forms for 
/// our django models, we cannot use django's form/template system. Instead,
/// we need to generate metadata about the model field structure and generate
/// the form webpage dynamically as the user fills it out.

/// We want to have forms that allow for submissions of one broad form, which 
/// splits its submitted data into multiple tables, supporting complex fields
/// which hook into models, evalutating the model field structure, and generate
/// appropriate subfields based on the model's field definitions.

/// For example, if we have one django model "Software" which contains 3 
/// subfields: a text input for its name, a M2M field pointing to another table,
/// and a third foreign key field also pointing to another table, we can 
/// generate that form structure of nested foreign table references as shown 
/// below in the example

/// EXAMPLE:

// types we will work with
type TextInput = any; // basic input field
type SerializedModel = {typeName: string, topField: string, subfields: Subfield[]};
type Subfield = {
    name: string, 
    type: string | SerializedModel, 
    multi: boolean 
} & {[key: string]: any};

// imagine we are given this data in this format:
const data: SerializedModel[] = [
    {
        typeName: "Software",
        topField: "name",
        subfields: [
            {
                name: "name",
                type: "TextInput",
                multi: false,
            },
            {
                name: "authors",
                type: "Person",
                multi: true,
            },
            {
                name: "funder",
                type: "Organization",
                multi: false,
            },
        ],
    },
    {
        typeName: "Person",
        topField: "name",
        subfields: [
            {
                name: "name",
                type: "TextInput",
                multi: false,
            },
            {
                name: "identifier",
                type: "TextInput",
                multi: false,
            },
            {
                name: "affiliations",
                type: "Organization",
                multi: true,
            }
        ],
    },
    {
        typeName: "Organization",
        topField: "name",
        subfields: [
            {
                name: "name",
                type: "TextInput",
                multi: false,
            },
            {
                name: "website",
                type: "TextInput",
                multi: false,
            },
            {
                name: "abbreviation",
                type: "TextInput",
                multi: false,
            },
        ],
    },
];

// Now we need to create a map that maps each object in that data list 
// to a name:
const modelMap: Map<string, SerializedModel> = new Map();
for(const model of data) modelMap.set(model.typeName, model);

// Now we can parse the models into proper fields
const parsedModels: SerializedModel[] = [];
for(const model of data){
    for(const subfield of model.subfields){

        // convert subfield types to the actual widget types
        if(typeof subfield.type === "string"){
            subfield.type = modelMap.get(subfield.type);
        }
    }
}