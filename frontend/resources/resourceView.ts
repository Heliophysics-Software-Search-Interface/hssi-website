/** 
 * a list-style display that shows users different software resource entries 
 * from within the HSSI database
 */
export class ResourceView {

    /** the html element that contains all the html content for this view */
    public containerElement: HTMLDivElement = null;

    public constructor() {
        this.containerElement = document.createElement("div");
    }
}