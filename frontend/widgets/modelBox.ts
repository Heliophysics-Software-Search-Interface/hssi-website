import { 
    Widget, widgetDataAttribute,
} from "./widget";

const optionDataValue = "json-options";

/** style class name for dropdown element */
const dropdownStyle = "widget-dropdown";

/** style class name for tooltip element */
const tooltipStyle = "widget-tooltip";

/// Types used for 

interface OptionLi extends HTMLLIElement { data: Option; }

interface Option {
	id: string;
	name: string;
	keywords: string[];
	tooltip?: string;
}

export class ModelBox extends Widget {
    
    private optionListElement: HTMLUListElement = null;
    private inputElement: HTMLInputElement = null;
    private inputContainerElement: HTMLElement = null;
    private inputContainerRowElement: HTMLElement = null;
    private dropdownButtonElement: HTMLButtonElement = null;
    
    private options: Option[] = null;
    private allOptionLIs: OptionLi[] = [];
    private filteredOptionLIs: OptionLi[] = [];
    private selectedOptionIndex: number = -1;
    
    /// Restricted functionality -----------------------------------------------

    private collectData(): void {

        // get the json data for the options
        this.options = 
            JSON.parse(
                this.element.querySelector(
                    `script[${widgetDataAttribute}=${optionDataValue}]`
                ).textContent
            );
    }

    private buildElements(): void {

        // create and populate the dropdown list
        this.allOptionLIs.length = 0;
        this.optionListElement = document.createElement("ul");
        for(const option of this.options) {
            const li: OptionLi = document.createElement("li") as any;
            li.data = option;
            this.allOptionLIs.push(li);
            this.optionListElement.appendChild(li);
        }

        // create the input, container, and row elements
        this.inputElement = document.createElement("input");
        this.inputElement.type = "text";
        this.inputContainerElement = document.createElement("div");
        this.inputContainerElement.appendChild(this.inputElement);
        this.inputContainerRowElement = document.createElement("div");
        this.inputContainerRowElement.append(this.inputContainerElement);
        this.element.appendChild(this.inputContainerRowElement);

        // add event listeners for the input
        this.inputElement.addEventListener("input", e => this.onInputValueChanged(e))
        this.inputElement.addEventListener("keydown", e => this.onInputKeyDown(e))

        // build dropdown button if applicable
        const dropdownButton = true;
        if(dropdownButton) this.buildDropdownButton();
    }

    private buildDropdownButton(): void {

        this.dropdownButtonElement = document.createElement("button");
        this.dropdownButtonElement.type = "button";
        this.dropdownButtonElement.style.position = "absolute";
        this.dropdownButtonElement.style.height = "100%";
        this.dropdownButtonElement.style.aspectRatio = "1";
        this.dropdownButtonElement.style.right = "0";
        this.dropdownButtonElement.style.top = "0";
        this.inputContainerElement.appendChild(this.dropdownButtonElement);
        this.dropdownButtonElement.addEventListener("click", _ => this.showDropdown());
    }

    private filterOptionVisibility(filterString: string = null) {

        // default to input value as filter
        if(filterString == null) filterString = this.inputElement.value;
		
        // TODO get property
        const caseSensitiveFilter = false;
		if (caseSensitiveFilter) {
            filterString = filterString.toLocaleUpperCase();
		}
        
        // iterate through each option li showing options that pass the 
        // filter while hiding others
		const splitInput = filterString.split(" ");
        this.filteredOptionLIs = [];
		for (const index in this.allOptionLIs) {
            const optionLi = this.allOptionLIs[index];
			const match = splitInput.every(
                word => optionLi.data.keywords.some(kw => kw?.includes(word))
            );
            const visible = (match || filterString.length <= 0);
			optionLi.style.display = visible ? "block" : "none";
			if (visible) this.filteredOptionLIs.push(optionLi);
		}
    }

    /** Implementation for {@link Widget.prototype.initialize} */
    protected initialize(): void {
        this.collectData();
        this.buildElements();
    }

    /// Event listeners --------------------------------------------------------

    private onInputValueChanged(_: Event): void {
        this.filterOptionVisibility();
    }

    private onInputKeyDown(keyEvent: KeyboardEvent): void {

        switch(keyEvent.key) {
            case "ArrowDown": 
                // TODO nav down style
                this.selectedOptionIndex += 1;
                if(this.selectedOptionIndex >= this.filteredOptionLIs.length) {
                    this.selectedOptionIndex = 0;
                }
                break;
            case "ArrowUp": 
                // TODO nav up style
                this.selectedOptionIndex -= 1;
                if(this.selectedOptionIndex < 0) {
                    this.selectedOptionIndex = this.filteredOptionLIs.length - 1;
                }
                break;
            case "Enter": 
                // TODO select nav option
                break;
			case " ":
				if (keyEvent.ctrlKey) {
					this.filterOptionVisibility();
				}
				break;
			case "Escape": 
                ModelBox.hideDropdown(); 
                break;
        }
    }

    /// Public functionality ---------------------------------------------------

    public showDropdown(): void {
        this.filterOptionVisibility();
        ModelBox.setDropdownList(this.optionListElement);
        ModelBox.setDropdownTarget(this);
        ModelBox.showDropdown(this.inputContainerElement);
    }

    /// Dropdown and tooltip elements ------------------------------------------

    private static dropdownElement: HTMLDivElement = null;
    private static tooltipElement: HTMLDivElement = null;

    private static createDropdownElement(): void {
        this.dropdownElement = document.createElement("div");
        this.dropdownElement.style.position = "absolute";
        this.dropdownElement.style.display = "none";
        this.dropdownElement.style.zIndex = "1000";
        this.dropdownElement.style.overflow = "hidden";
        document.body.appendChild(this.dropdownElement);
    }

    private static createTooltipElement(): void {
        this.tooltipElement = document.createElement("div");
        this.dropdownElement.style.position = "absolute";
        this.tooltipElement.style.display = "none";
        this.dropdownElement.style.zIndex = "2000";
        this.dropdownElement.style.pointerEvents = "none";
        document.body.appendChild(this.tooltipElement);
    }

    protected static getDropdownElement(): HTMLDivElement {
        if(this.dropdownElement == null) this.createDropdownElement();
        return this.dropdownElement;
    }

    protected static getTooltipElement(): HTMLDivElement {
        if(this.tooltipElement == null) this.createTooltipElement();
        return this.tooltipElement;
    }

    private static positionDropdownElement(target: HTMLElement): void {
		const rect = target.getBoundingClientRect();
		this.dropdownElement.style.left = `${rect.left + window.scrollX}px`;
		this.dropdownElement.style.top = `${rect.bottom + window.scrollY}px`;
		this.dropdownElement.style.width = `${rect.width}px`;
		this.dropdownElement.style.display = "block";
    }

    /**
     * display the dropdown menu to appear as if it is coming from the 
     * specified element
     */
    private static showDropdown(from: HTMLElement) {
        this.positionDropdownElement(from);
        this.dropdownElement.style.display = "block";
    }

    /**
     * set the content inside the dropdown menu
     * @param list the list of LIs that will be displayed within the dropdown
     */
    private static setDropdownList(list: HTMLUListElement) {

        // clear previous content
        while(this.dropdownElement.firstChild) {
            // TODO remove events
            this.dropdownElement.removeChild(this.dropdownElement.firstChild)
        }

        // add new content
        // TODO attach events
        this.dropdownElement.appendChild(list);
    }

    /**
     * set the instance for the dropdown menu to focus on for various context
     * related actions
     * @param target the target instance to use
     */
    private static setDropdownTarget(target: ModelBox) {
        // TODO
    }

    public static hideDropdown() {
        this.dropdownElement.style.display = "none";
    }

    /**
     * display the tooltip at the specified position
     * @param xPos x coordinate of tooltip position in px
     * @param yPos y coord in px
     * @param text the text to display in tooltip
     */
    public static showTooltip(xPos: number, yPos: number, text: string): void {
        // TODO
    }
}