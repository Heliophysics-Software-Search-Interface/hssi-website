import { 
    Widget, widgetDataAttribute,
} from "./widget";

const optionDataValue = "json-options";

/** style class name for dropdown element */
const dropdownStyle = "widget-dropdown";

/** style class name for tooltip element */
const tooltipStyle = "widget-tooltip";

const dropButtonStyle = "dropdown-button";

const selectedStyle = "selected";

/// Organizational types -------------------------------------------------------

interface OptionLi extends HTMLLIElement { data: Option; }

interface Option {
	id: string;
	name: string;
	keywords: string[];
	tooltip?: string;
}

/// Main defintion -------------------------------------------------------------

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
    private selectedOptionLI: OptionLi = null;
    
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
            li.tabIndex = 0;
            li.style.position = "relative";
            li.style.display = "inline-block";
			li.style.userSelect = "none";
            
            li.innerText = option.name;
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

        // add event listeners
        this.optionListElement.addEventListener("click", e => this.onListClick(e));
        this.optionListElement.addEventListener("mouseover", e => this.onListMouseover(e));
        this.inputElement.addEventListener("input", e => this.onInputValueChanged(e));
        this.inputElement.addEventListener("keydown", e => this.onInputKeyDown(e));
        this.inputContainerElement.addEventListener("focusin", e => this.onInputFocusIn(e));
        this.inputContainerElement.addEventListener("focusout", e => this.onInputFocusOut(e));

        // build dropdown button if applicable
        // TODO dropdown button property
        const dropdownButton = true;
        if(dropdownButton) this.buildDropdownButton();
    }

    private buildDropdownButton(): void {

        this.dropdownButtonElement = document.createElement("button");
        this.dropdownButtonElement.type = "button";
        this.dropdownButtonElement.innerText = "▼";
        this.dropdownButtonElement.classList.add(dropButtonStyle);
        this.dropdownButtonElement.style.position = "absolute";
        this.dropdownButtonElement.style.height = "100%";
        this.dropdownButtonElement.style.aspectRatio = "1";
        this.dropdownButtonElement.style.right = "0";
        this.dropdownButtonElement.style.top = "0";
        this.inputContainerElement.appendChild(this.dropdownButtonElement);
        this.dropdownButtonElement.addEventListener("click", e => this.onDropdownButtonClick(e));
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
			const match = splitInput.some(
                word => optionLi.data.keywords.some(kw => kw?.includes(word))
            );
            const visible = (match || filterString.length <= 0);
			optionLi.style.display = visible ? "block" : "none";
			if (visible) this.filteredOptionLIs.push(optionLi);
		}
    }

    protected setSelectedOptionLI(option: OptionLi): void {
        
        // remove the previously selected class from the selected li if 
        // there is one
        if(this.selectedOptionLI != null){
            this.selectedOptionLI.classList.remove(selectedStyle);
        }

        // add selected style to newly selected option and scroll it into view
        if(option != null && option.style.display !== "none"){
            option.classList.add(selectedStyle);
            option.scrollIntoView({ behavior: "instant", block: "nearest" });
            const index = this.filteredOptionLIs.indexOf(option);
            this.selectedOptionIndex = index;
        }
        else {
            // set option index to -1 if selecting null or invalid li
            this.selectedOptionIndex = -1;
        }

        this.selectedOptionLI = option;
    }

    /** Implementation for {@link Widget.prototype.initialize} */
    protected initialize(): void {
        this.collectData();
        this.buildElements();
    }

    /// Event listeners --------------------------------------------------------

    private onDropdownButtonClick(_: Event): void {
        this.inputElement.focus();
    }

    private onListClick(event: Event): void {
        const clickedOption = event.target;
        // TODO handle selecting clicked option
        if(clickedOption instanceof HTMLLIElement){
            this.setSelectedOptionLI(clickedOption as OptionLi);
        }
        ModelBox.hideDropdown();
    }

    private onListMouseover(event: MouseEvent): void {
        const option = event.target;
        if(option instanceof HTMLLIElement){
            this.setSelectedOptionLI(option as OptionLi);
        }
    }

    private onInputValueChanged(_: Event): void {
        this.filterOptionVisibility();
    }

    private onInputKeyDown(keyEvent: KeyboardEvent): void {

        switch(keyEvent.key) {
            case "ArrowDown": 
                if(ModelBox.isDropdownVisible()){
                    this.selectedOptionIndex += 1;
                    if(this.selectedOptionIndex >= this.filteredOptionLIs.length) {
                        this.selectedOptionIndex = 0;
                    }
                    this.setSelectedOptionLI(this.filteredOptionLIs[this.selectedOptionIndex]);
                }
                break;
            case "ArrowUp": 
                if(ModelBox.isDropdownVisible()){
                    this.selectedOptionIndex -= 1;
                    if(this.selectedOptionIndex < 0) {
                        this.selectedOptionIndex = this.filteredOptionLIs.length - 1;
                    }
                    this.setSelectedOptionLI(this.filteredOptionLIs[this.selectedOptionIndex]);
                }
                break;
            case "Enter": 
                if(ModelBox.isDropdownVisible()){
                    keyEvent.preventDefault();
                    // TODO select nav option
                }
                break;
			case " ":
				if (keyEvent.ctrlKey && !ModelBox.isDropdownVisible()) {
                    this.showDropdown();
				}
				break;
			case "Escape": 
                ModelBox.hideDropdown(); 
                break;
        }
    }

    private onInputFocusIn(focusEvent: FocusEvent): void {
        if(ModelBox.isDropdownVisible()) ModelBox.hideDropdown();
        this.showDropdown();
    }

    private onInputFocusOut(focusEvent: FocusEvent): void {
        const newFocus = focusEvent.relatedTarget;

        // we only want to hide the dropdown if something in the dropdown 
        // isn't what's being focused
        if(!newFocus || !this.allOptionLIs.includes(newFocus as any)){
            ModelBox.hideDropdown();
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

    protected static getDropdownElement(): HTMLDivElement {
        if(this.dropdownElement == null) this.createDropdownElement();
        return this.dropdownElement;
    }

    protected static getTooltipElement(): HTMLDivElement {
        if(this.tooltipElement == null) this.createTooltipElement();
        return this.tooltipElement;
    }

    private static createDropdownElement(): void {
        this.dropdownElement = document.createElement("div");
        this.dropdownElement.classList.add(dropdownStyle);
        this.dropdownElement.style.display = "none";
        this.dropdownElement.style.overflow = "hidden";
        this.dropdownElement.style.position = "absolute";
        this.dropdownElement.style.borderTop = "none";
        this.dropdownElement.style.zIndex = "1000";
        this.dropdownElement.style.listStyle ="none";
        this.dropdownElement.style.maxHeight = "200px";
        this.dropdownElement.style.overflowY = "auto";
        
        document.body.appendChild(this.dropdownElement);
    }

    private static createTooltipElement(): void {
        this.tooltipElement = document.createElement("div");
        this.tooltipElement.style.position = "absolute";
        this.tooltipElement.style.display = "none";
        this.tooltipElement.style.zIndex = "2000";
        this.tooltipElement.style.pointerEvents = "none";
        document.body.appendChild(this.tooltipElement);
    }

    private static positionDropdownElement(target: HTMLElement): void {
        const dropdown = this.getDropdownElement();
		const rect = target.getBoundingClientRect();
		dropdown.style.left = `${rect.left + window.scrollX}px`;
		dropdown.style.top = `${rect.bottom + window.scrollY}px`;
		dropdown.style.width = `${rect.width}px`;
		dropdown.style.display = "block";
    }

    private static isDropdownVisible(): boolean {
        return this.getDropdownElement().style.display !== "none";
    }

    /**
     * display the dropdown menu to appear as if it is coming from the 
     * specified element
     */
    private static showDropdown(from: HTMLElement): void {
        this.positionDropdownElement(from);
        this.getDropdownElement().style.display = "block";
    }

    /**
     * set the content inside the dropdown menu
     * @param list the list of LIs that will be displayed within the dropdown
     */
    private static setDropdownList(list: HTMLUListElement): void {

        // clear previous content
        const dropdown = this.getDropdownElement();
        while(dropdown.firstChild) {
            dropdown.removeChild(dropdown.firstChild)
        }

        // add new content
        dropdown.appendChild(list);
    }

    /**
     * set the instance for the dropdown menu to focus on for various context
     * related actions
     * @param target the target instance to use
     */
    private static setDropdownTarget(target: ModelBox): void {
        // TODO
    }

    public static hideDropdown(): void {
        this.getDropdownElement().style.display = "none";
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