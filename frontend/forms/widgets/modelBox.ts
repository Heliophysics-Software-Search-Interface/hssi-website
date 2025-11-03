import { 
	Widget, widgetDataAttribute,
	type AnyInputElement,
	type BaseProperties,
	getStringSimilarity,
	type JSONObject,
	fetchTimeout,
	FormGenerator,
	ModelMultiSubfield,
	type ModelName
} from "../../loader";

const optionDataValue = "json-options";

// style names for managed elements
const dropdownStyle = "widget-dropdown";
const tooltipStyle = "widget-tooltip";
const dropButtonStyle = "dropdown-button";
const selectedStyle = "selected";
const optionValidStyle = "option-valid";

const modelsUrl = "/api/models/";
const modelChoicesSlug = "/choices/";
const modelRowSlug = "/rows/";

type ChoicesJsonStructure = { data: [string, string, string[], string?][] }

interface ModelBoxProperties extends BaseProperties {
	targetModel?: ModelName,
	modelFilter?: string,
	dropdownButton?: string,
	allowNewEntries?: string,
	licenseModelbox?: boolean,
}

/// Organizational types -------------------------------------------------------

interface OptionLi extends HTMLLIElement { data: Option; }

interface Option extends JSONObject {
	id: string;
	name: string;
	keywords: string[];
	tooltip?: string;
}

/// Main defintion -------------------------------------------------------------

export class ModelBox extends Widget {
	
	private optionListElement: HTMLUListElement = null;
	private inputElement: HTMLInputElement & {data?: JSONObject} = null;
	private inputContainerElement: HTMLElement = null;
	private inputContainerRowElement: HTMLElement = null;
	private dropdownButtonElement: HTMLButtonElement = null;
	
	public options: Option[] = null;
	private allOptionLIs: OptionLi[] = [];
	private filteredOptionLIs: OptionLi[] = [];
	private selectedOptionIndex: number = -1;
	private selectedOptionLI: OptionLi = null;
	private listenerUnset: (x: any) => any = null;
	private listenerUnsetChild: (x: any) => any = null;

	public properties: ModelBoxProperties = {};
	public rowFetchAbort: AbortController = null;
	
	/// Restricted functionality -----------------------------------------------

	private buildElements(readOnly: boolean): void {

		// create and populate the dropdown list
		if(this.options != null) this.buildOptions(this.options);
		if(this.properties.targetModel){
			this.buildOptionsFromModel(this.properties.targetModel);
		}

		// create the input, container, and row elements
		this.inputElement = document.createElement("input");
		this.inputElement.type = "text";
		this.inputElement.readOnly = readOnly;
		this.inputContainerElement = document.createElement("div");
		this.inputContainerElement.appendChild(this.inputElement);
		this.inputContainerRowElement = document.createElement("div");
		this.inputContainerRowElement.append(this.inputContainerElement);
		this.element.appendChild(this.inputContainerRowElement);

		// enforce max length
		const maxLength = this.properties?.maxLength ?? 100;
		this.inputElement.setAttribute("maxlength", maxLength.toString());

		// add event listeners
		if(!readOnly){
			this.inputElement.addEventListener("input", e => this.onInputValueChanged(e));
			this.inputElement.addEventListener("keydown", e => this.onInputKeyDown(e));
			this.inputContainerElement.addEventListener("focusin", e => this.onInputFocusIn(e));
			this.inputContainerElement.addEventListener("focusout", e => this.onInputFocusOut(e));
		}

		// build dropdown button if applicable
		if(this.properties.dropdownButton && !readOnly) this.buildDropdownButton();

		if(this.parentField){
			this.listenerUnset = this.parentField.onValueChanged.addListener(() => {
				this.unsetInputElementData();
			});

			this.listenerUnsetChild = this.parentField.onChildValueChanged.addListener(() => {
				this.unsetInputElementData();
			});
		}
	}

	private unsetInputElementData(): void{
		const elem = this.getInputElement();
		if(elem.data) {
			elem.data = null;
			this.updateValidModelStyle();
		}
	}

	private updateValidModelStyle(): void{
		const elem = this.getInputElement();
		if(elem.data) elem.classList.add(optionValidStyle);
		else elem.classList.remove(optionValidStyle);
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
			let visible = (match || filterString.length <= 0);
			if (this.properties.licenseModelbox){
				if(
					optionLi.data.name.toUpperCase() == "OTHER" && 
					optionLi.data.keywords.length > 1
				)
					visible = false;
			}
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

	protected fetchModelRow(uid: string): void {
		this.rowFetchAbort?.abort();
		this.rowFetchAbort = null;

		// fetch object data to fill out
		const fetchUrl = modelsUrl + this.properties.targetModel + modelRowSlug + uid;
		this.rowFetchAbort = new AbortController();
		console.log(`Fetching ${this.properties.targetModel} row: ${uid}`);
		const promise = fetch(fetchUrl, { signal: this.rowFetchAbort.signal });
		promise.then(async data => {
			// console.log(data);
			const jsonData = await data.json();
			const collapse = !this.parentField.subfieldsExpanded();
			this.parentField.expandSubfields();
			if(collapse) this.parentField.collapseSubfields();
			const subfields = this.parentField.getSubfields();
			// console.log(jsonData);
			for(const dataFieldName in jsonData){
				const subfield = subfields.find(x => {
					const mappedName = FormGenerator.fieldMap[x.name] ?? "NONE";
					return mappedName == dataFieldName;
				});
				// const msg = dataFieldName + "->" + subfield?.name + " : ";
				// console.log(msg, jsonData[dataFieldName]);
				if(subfield){
					const jsonValue = jsonData[dataFieldName];
					if(subfield instanceof ModelMultiSubfield) {
						if(jsonValue instanceof Array)
							subfield.fillMultiFields(jsonValue, false);
						else subfield.fillMultiFields([jsonValue], false);
					}
					else subfield.fillField(jsonValue, false);
				}
			}
			this.rowFetchAbort = null;
		});
		promise.catch(err => console.error(err));
	}

	public selectOption(option: Option = this.selectedOptionLI?.data): void {
		this.rowFetchAbort?.abort();
		this.rowFetchAbort = null;
		if(option != null){
			this.inputElement.value = option.name;
			this.inputElement.data = option;
			// this.inputElement.dispatchEvent(new Event("input", { bubbles: true }));
			this.parentField?.requirement.applyRequirementWarningStyles();
			this.fetchModelRow(option.id);
		}
		else {
			this.inputElement.data = null;
		}
		this.updateValidModelStyle();
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
		const jsonElem = this.element.querySelector(
			`script[${widgetDataAttribute}=${optionDataValue}]`
		);
		if(jsonElem != null) this.options = JSON.parse(jsonElem.textContent);
	}

	/** @override Implementation for {@link Widget.prototype.initialize} */
	public initialize(readOnly: boolean = false): void {
		super.initialize(readOnly);
		this.buildElements(readOnly);
	}

	/* builds the option element list from the given options */
	private buildOptions(options: Option[]): void {

		// enforce case insensitivity for keyword filtering
		this.options = options;
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

		// reset options
		if(this.optionListElement != null) this.optionListElement.remove();
		this.allOptionLIs.length = 0;
		this.filteredOptionLIs.length = 0;
		this.selectedOptionIndex = -1;

		// move "other" option to last in the list
		// TODO add as property for moving any named item to bottom of list
		let otherIndex = options.findIndex(x => {
			if(x == null) return false;
			return "other" == x.name.trim().toLocaleLowerCase();
		});
		if(otherIndex >= 0){
			options.push(options.splice(otherIndex, 1)[0]);
		}

		// move "x independent" option to first in the list
		// TODO add as property for moving any named item to top of list
		if(this.properties.targetModel === "OperatingSystem"){
			let independentIndex = options.findIndex(x => {
				return x.name.toUpperCase().includes("INDEPENDENT");
			});
			if (independentIndex >= 1){
				options.splice(0, 0, ...options.splice(independentIndex, 1));
			}
		}

		// create and populate the dropdown list
		this.optionListElement = document.createElement("ul");
		for(const option of this.options) {
			if(option == null) continue;
			const li: OptionLi = document.createElement("li") as any;
			li.data = option;
			li.tabIndex = 0;
			li.style.position = "relative";
			li.style.display = "inline-block";
			li.style.userSelect = "none";
			
			li.innerText = option.name;
			this.allOptionLIs.push(li);
		}
		this.allOptionLIs.sort((a, b) => a.data.name.localeCompare(b.data.name));
		for(const li of this.allOptionLIs) this.optionListElement.appendChild(li);

		this.optionListElement.addEventListener("click", e => this.onListClick(e));
		this.optionListElement.addEventListener("mouseover", e => this.onListMouseover(e));
	}

	/**
	 * gets the choice data from the specified model and builds it's own 
	 * options list based off that
	 */
	private async buildOptionsFromModel(modelName: ModelName): Promise<void> {
		let optionData: Option[] = ModelBox.optionMap.get(modelName);
		if(!optionData){
			const data: ChoicesJsonStructure = await (
				await fetchTimeout(modelsUrl + modelName + modelChoicesSlug)
			).json();
			optionData = data.data.map(x => {
				if(x == null) return null;
				return {
					id: x[0],
					name: x[1],
					keywords: x[2],
					tooltip: x[3],
				}
			});
			ModelBox.optionMap.set(modelName, optionData);
		}
		this.buildOptions(optionData);
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
		if(this.properties.dropdownButton){
			this.filterOptionVisibility("");
		}
		if(this.properties.dropdownButton){
			this.showDropdown(!this.properties.dropdownButton);
		}
	}

	private onInputFocusOut(focusEvent: FocusEvent): void {
		const newFocus = focusEvent.relatedTarget;

		// we only want to hide the dropdown if something in the dropdown 
		// isn't what's being focused
		if(!newFocus || !this.allOptionLIs.includes(newFocus as any)){
			ModelBox.hideDropdown();
		}
	}

	private findMatchingOption(value: string, threshold: number = 0): Option {
		if(!this.options) return null;

		let option: Option = null;
		let matchScore: number = threshold;
		for(let i = this.options.length - 1; i >= 0; i--){
			const opdata = this.options[i];
			if(value in opdata.keywords){
				return opdata;
			}

			// choose the option with the greatest likeness score
			const likeness = getStringSimilarity(opdata.name, value);
			if(likeness >= 1) return opdata;
			if(likeness > matchScore){
				option = opdata;
				matchScore = likeness;
			}
		}

		if(option) console.log(`Matched ${value} with ${option.name}, likeness: ${matchScore}`);
		return option;
	}

	/// Public functionality ---------------------------------------------------

	public override setValue(value: string, notify: boolean = true): void {
		if(!this.options) {
			super.setValue(value);
			this.buildOptionsFromModel(this.properties.targetModel).then(
				() => this.setValue(value, notify)
			);
			return;
		}

		const matchThreshold = this.properties.allowNewEntries ? 1 : 0;
		const match = this.findMatchingOption(value, matchThreshold);
		if(match) {
			super.setValue(match.name, notify);
			this.inputElement.data = match;
		}
		else {
			if(this.properties.allowNewEntries) super.setValue(value);
			else super.setValue("");
			this.inputElement.data = null;
		}
	}

	public showDropdown(filter: boolean = true): void {
		this.setSelectedOptionLI(null);
		if(filter) this.filterOptionVisibility();
		ModelBox.setDropdownList(this.optionListElement);
		ModelBox.setDropdownTarget(this);
		ModelBox.showDropdown(this.inputContainerElement);
	}

	public getInputElement(): AnyInputElement { return this.inputElement; }

	override getInputValue(): string {
		const inputElem = this.getInputElement();
		if(inputElem?.data?.id){
			return inputElem.data.id as string;
		}
		return super.getInputValue();
	}

	override destroy(): void {
		if(this.parentField){
			this.parentField.onValueChanged.removeListener(this.listenerUnset);
			this.parentField.onChildValueChanged.removeListener(this.listenerUnsetChild);
		}
		super.destroy();
	}

	/// Dropdown and tooltip elements ------------------------------------------

	protected static optionMap: Map<string, Option[]> = new Map();
	private static dropdownElement: HTMLDivElement = null;
	private static tooltipElement: HTMLDivElement = null;
	private static repositionDropdownInterval: number = 0;

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
		this.repositionDropdownInterval = setInterval(() => this.showDropdownRecurse(from), 100);
		this.showDropdownRecurse(from);
	}

	private static showDropdownRecurse(from: HTMLElement): void{
		if(this.repositionDropdownInterval){
			this.positionDropdownElement(from);
			this.getDropdownElement().style.display = "block";
		}
	}

	/**
	 * set the content inside the dropdown menu
	 * @param list the list of LIs that will be displayed within the dropdown
	 */
	private static setDropdownList(list: HTMLUListElement): void {

		// clear previous content
		const dropdown = this.getDropdownElement();
		while(dropdown.firstChild) dropdown.removeChild(dropdown.firstChild);

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
		if(this.repositionDropdownInterval){
			clearInterval(this.repositionDropdownInterval);
			this.repositionDropdownInterval = 0;
		}
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