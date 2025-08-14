/**
 * represents a single software resource submitted to the HSSI database, 
 * rendered to html for the user to interactwith
 */
export class ResourceItem{

    /** the html element that contains all the html content for this item */
    public containerElement: HTMLDivElement = null;

    constructor(){
        this.containerElement = document.createElement("div");
    }
}