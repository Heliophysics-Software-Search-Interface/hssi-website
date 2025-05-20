/**
 * Handles model object selector widgets frontend logic
 */

import { 
	Widget, propertiesType, uidAttribute, typeAttribute 
} from "../loader";

const choicesType = "json-choices";
const tooltipType = "option-tooltip";
const dropdownButtonType = "dropdown-button";

/** Interface representing a selectable choice */
interface Choice {
	id: string;
	name: string;
	keywords: string[];
	tooltip?: string;
}

interface ChoiceLi extends HTMLLIElement {
	data: Choice;
}

/**
 * ModelObjectSelector widget class.
 * Manages filtering, selection, and tooltips for a dropdown widget UI.
 */
export class ModelObjectSelector extends Widget {
	/** Collection of all initialized ModelObjectSelector instances */
	public static widgets: ModelObjectSelector[] = [];

	private uid: string = "";
	private input: HTMLInputElement = null;
	private optionList: HTMLUListElement = null;
	private tooltip: HTMLDivElement = null;
	private filteredOptions: HTMLLIElement[] = [];
	private selectedOption: number = -1;
	private allChoices: Choice[] = [];
	private allInputs: HTMLInputElement[] = [];

	protected setDefaultProperties(): void {
		this.properties = {
			caseSensitiveFiltering: false,
    		multiSelect: false,
    		filterOnFocus: true,
    		dropdownOnFocus: true,
    		dropdownOnBlank: false,
    		dropdownButton: false,
    		optionTooltips: true,
    		newObjectField: null,
		};
	}

	/** Initialize the widget instance */
	protected initialize(): void {
		if (!this.element) return;
		ModelObjectSelector.widgets.push(this);

		// get properties and uuid from data attributes
		this.uid = this.element.getAttribute(uidAttribute);
		this.properties = JSON.parse(
			this.element.querySelector<HTMLOrSVGScriptElement>(
				`script[${typeAttribute}=${propertiesType}]`
			).textContent
		);

		// find option list element and properly append it
		this.optionList = this.element.querySelector("ul") as HTMLUListElement;
		this.optionList.remove();
		document.body.appendChild(this.optionList);

		// find dropdown button and remove it if disabled
		const dropdownButton = this.element.querySelector<HTMLButtonElement>(
			`button[${typeAttribute}=${dropdownButtonType}]`
		);
		if(!this.properties.dropdown_button) dropdownButton.remove();

		// find input element to use
		this.input = this.element.querySelector("input") as HTMLInputElement;
		this.input.removeAttribute("autocomplete");
		this.input.spellcheck = false;
		this.allInputs.push(this.input);

		// find the tooltip element
		this.tooltip = this.element.querySelector(
			`[${typeAttribute}=${tooltipType}]`
		) as HTMLDivElement;

		// gather the choices from the element
		this.allChoices = JSON.parse(
			this.element.querySelector<HTMLScriptElement>(
				`script[${typeAttribute}=${choicesType}]`
			).textContent
		);

		if (!this.properties.case_sensitive_filtering) {
			for (const choice of this.allChoices) {
				choice.keywords = choice.keywords.map(k => k?.toLocaleUpperCase());
			}
		}
		this.createChoiceLIs();
		this.addEvents(this.input.parentElement);
	}

	private createChoiceLIs(): void {
		this.allChoices.forEach(choice => {
			const li = document.createElement("li") as ChoiceLi;
			li.tabIndex = 0;
			li.style.userSelect = "none";
			li.style.display = "none";
			li.data = choice;
			li.innerText = choice.name;
			this.optionList.appendChild(li);

			li.addEventListener("click", () => this.selectOption(li, false));
			if (this.properties.option_tooltips) {
				li.title = choice.tooltip || "";
				li.addEventListener("mouseenter", () => this.showTooltip(li));
				li.addEventListener("mouseout", () => this.hideTooltip());
			}
		});
	}

	private addEvents(container: HTMLElement): void {
		const input = container.querySelector<HTMLInputElement>("input");
		input.addEventListener("focus", e => this.handleFocusIn(e));
		input.addEventListener("input", e => this.handleFocusIn(e));
		input.addEventListener("focusout", e => this.handleFocusOut(e));
		input.addEventListener("keydown", e => this.handleKeyNav(e));

		if(this.properties.dropdown_button) {
			const button = container.querySelector<HTMLButtonElement>("button");
			button.addEventListener("click", e => this.handleFocusIn(e))
		}
	}

	/** Handles input focus or input event */
	private handleFocusIn(e: Event): void {
		const isFocusEvt = e instanceof FocusEvent;
		let target: HTMLInputElement = e.target as any;
		if (!(e.target instanceof HTMLInputElement)) {
			target = target.parentElement.querySelector<HTMLInputElement>("input");
			target.focus();
			return;
		}
		this.input = target;
		if (this.properties.dropdown_on_focus || !isFocusEvt) {
			const filterStr = isFocusEvt && !this.properties.filter_on_focus ? "" : null;
			if (this.properties.dropdown_on_blank || this.input.value.length > 0) {
				this.filterOptions(filterStr);
			} else {
				this.hideOptions();
			}
		}
	}

	/** Handles input focus out event */
	private handleFocusOut(e: FocusEvent): void {
		const target = e.target as HTMLElement;
		const focusTarget = e.relatedTarget;
		if (!focusTarget || !this.optionList.contains(focusTarget as HTMLUListElement)) {
			this.hideOptions();
		}
	}

	/** Handles arrow key navigation and enter/space behavior */
	private handleKeyNav(evt: KeyboardEvent): void {
		let optionChanged = -1;
		switch (evt.key) {
			case "ArrowDown":
				if (this.optionList.style.display !== "none") {
					optionChanged = this.selectedOption;
					this.selectedOption = (this.selectedOption + 1) % this.filteredOptions.length;
				}
				break;

			case "ArrowUp":
				if (this.optionList.style.display !== "none") {
					optionChanged = this.selectedOption;
					this.selectedOption = (
						this.selectedOption - 1 + this.filteredOptions.length
					) % this.filteredOptions.length;
				}
				break;

			case "Enter":
				if (this.selectedOption >= 0) {
					this.selectOption(this.filteredOptions[this.selectedOption]);
				} else {
					this.confirmInput();
				}
				evt.preventDefault();
				break;

			case " ":
				if (evt.ctrlKey) {
					this.filterOptions();
				}
				break;

			case 'Backspace':
				if(this.input.value.length <= 0 && this.allInputs.length > 1) {
					let index = this.allInputs.indexOf(evt.target as any);
					if(index <= 0){
						this.allInputs[1].focus();
					}
					else {
						index -= 1;
						this.allInputs[index].focus();
					}
				}
				break;
			
			case "Escape":
				this.hideOptions();
				break;
		}
		if (this.selectedOption >= 0 && optionChanged !== this.selectedOption) {
			if (optionChanged >= 0) {
				this.filteredOptions[optionChanged].classList.remove("highlighted");
			}
			const option = this.filteredOptions[this.selectedOption];
			option.scrollIntoView({ block: "nearest" });
			option.classList.add("highlighted");
		}
	}

	/** Filters dropdown options based on input */
	private filterOptions(filterStr: string | null = null): void {
		if (this.selectedOption >= 0) {
			this.filteredOptions[this.selectedOption].classList.remove("highlighted");
		}
		this.selectedOption = -1;
		this.filteredOptions = [];
		
		let inputVal = filterStr !== null ? filterStr : this.input.value;
		if (!this.properties.case_sensitive_filtering) {
			inputVal = inputVal.toLocaleUpperCase();
		}

		const splitInput = inputVal.split(" ");
		const children = Array.from(this.optionList.children) as HTMLLIElement[];

		for (const option of children) {
			const data = (option as ChoiceLi).data;
			const match = splitInput.some(word => data.keywords.some(kw => kw?.includes(word)));
			option.style.display = (match || inputVal.length <= 0) ? "block" : "none";
			if (option.style.display === "block") this.filteredOptions.push(option);
		}

		const rect = this.input.getBoundingClientRect();
		this.optionList.style.left = `${rect.left + window.scrollX}px`;
		this.optionList.style.top = `${rect.bottom + window.scrollY}px`;
		this.optionList.style.width = `${rect.width}px`;
		this.optionList.style.display = "block";
	}

	/** Hides the dropdown list */
	private hideOptions(): void {
		this.optionList.style.display = "none";
		this.hideTooltip();
	}

	/** Handles when a user selects an option */
	private selectOption(option: HTMLLIElement, focusNext: boolean = true): void {
		const data = (option as ChoiceLi).data;
		this.input.value = data.name;
		this.input.setAttribute("data-id", data.id);
		option.classList.remove("highlighted");
		this.selectedOption = -1;
		this.hideOptions();
		this.confirmInput(focusNext);
	}

	/** Finalizes input value, adds input if multiselect is enabled */
	private confirmInput(focusNext: boolean = true): void {
		if (this.properties.multi_select) {
			const lastInput = this.allInputs[this.allInputs.length - 1];
			if (this.input !== lastInput) {
				this.input = lastInput;
			} else {
				const clone = this.input.parentElement.cloneNode(true) as HTMLElement;
				this.addEvents(clone);
				const newInput = clone.querySelector("input")!;
				newInput.value = "";
				this.input.parentElement.parentElement.appendChild(clone);
				this.allInputs.push(newInput);
				if(focusNext) this.input = newInput;
			}
			if(focusNext){
				this.input.focus();
				this.hideOptions();
			}
		} else {
			this.input.setAttribute("data-id", "-1");
			this.hideOptions();
		}
	}

	/** Shows a tooltip near the hovered option */
	private showTooltip(option: HTMLLIElement): void {
		const rect = option.getBoundingClientRect();
		this.tooltip.style.left = `${rect.right + window.scrollX + 10}px`;
		this.tooltip.style.top = `${rect.top + window.scrollY}px`;
		this.tooltip.style.display = "block";
	}

	/** Hides the tooltip */
	private hideTooltip(): void {
		this.tooltip.style.display = "none";
	}
}
