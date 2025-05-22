import { 
    Widget, widgetDataAttribute, targetUuidAttribute
} from "../loader";

const optionDataValue = "json-options";

// style names for managed elements
const dropdownStyle = "widget-dropdown";
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
        if(this.properties.dropdownButton) this.buildDropdownButton();
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
		
        // 
		if (!this.properties.caseSensitiveFilter) {
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

        // deselect if the selected option is filtered out
        if(this.selectedOptionLI?.style.display === "none"){
            this.setSelectedOptionLI(null);
        }

        // hide dropdown if no options are visible
        if(this.filteredOptionLIs.length <= 0) {
            ModelBox.hideDropdown();
        }
    }

    private confirmInput(): void {
        const targetUuid = this.inputElement.getAttribute(targetUuidAttribute);
        if(targetUuid == null) {
            this.inputElement.setAttribute(targetUuidAttribute, "0");
        }
    }

    protected selectOption(option: Option = this.selectedOptionLI?.data): void {
        if(option != null){
            this.inputElement.value = option.name;
            this.inputElement.setAttribute(targetUuidAttribute, option.id);
        }
        else {
            this.inputElement.removeAttribute(targetUuidAttribute);
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
    
    /** @override Implementation for {@link Widget.prototype.collectData} */
    protected collectData(): void {
        super.collectData();

        // get the json data for the options
        this.options = 
            JSON.parse(
                this.element.querySelector(
                    `script[${widgetDataAttribute}=${optionDataValue}]`
                ).textContent
            );
        
        // enforce case insensitivity for keyword filtering
        if(!this.properties.caseSensitiveFilter) {
            for(let i0 = this.options.length - 1; i0 >= 0; i0--) {
                if(this.options[i0] == null) continue;
                for(let i1 = this.options[i0].keywords.length - 1; i1 >= 0; i1--) {
                    if(this.options[i0].keywords[i1] == null) continue;
                    this.options[i0].keywords[i1] = (
                        this.options[i0].keywords[i1].toLocaleUpperCase()
                    );
                }
            }
        }
    }

    /** @override Implementation for {@link Widget.prototype.initialize} */
    protected initialize(): void {
		super.initialize();
        this.buildElements();
    }

    /// Event listeners --------------------------------------------------------

    private onDropdownButtonClick(_: Event): void {
        this.inputElement.focus();
    }

    private onListClick(event: Event): void {
        const clickedOption = event.target;
        if(clickedOption instanceof HTMLLIElement){
            this.setSelectedOptionLI(clickedOption as OptionLi);
            this.selectOption();
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
        this.selectOption(null);
        this.filterOptionVisibility();
        if(!ModelBox.isDropdownVisible() && this.filteredOptionLIs.length > 0){
            this.showDropdown();
        }
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
                keyEvent.preventDefault();
                if(ModelBox.isDropdownVisible() && this.selectedOptionIndex >= 0){
                    this.selectOption();
                }
                else {
                    this.confirmInput();
                }
                ModelBox.hideDropdown();
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

        this.confirmInput();
    }

    /// Public functionality ---------------------------------------------------

    public showDropdown(): void {
        this.setSelectedOptionLI(null);
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
        this.tooltipElement.classList.add(tooltipStyle);
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