/**
 * Module that handles definition of base class for all widgets
 */

import { 
	ModelSubfield, requirementAttributeContainer, RequirementLevel, SimpleEvent,
	type JSONObject,
	type JSONValue
} from "../../loader";

// names of values in data attributes
export const propertiesDataValue = "json-properties";

// names of attributes on html element that specify widget information
export const uidAttribute = "data-hssi-uid";
export const widgetAttribute = "data-hssi-widget";
export const widgetDataAttribute = "data-hssi-data";
export const typeAttribute = "data-hssi-type";

export interface BaseProperties extends Record<string, any> {
	requirementLevel?: RequirementLevel;
	maxLength?: number;
	autofillSiblings?: boolean;
}

export type AnyInputElement = (
	HTMLInputElement |
	HTMLTextAreaElement |
	HTMLSelectElement
) & { data?: JSONObject }

export type WidgetType = new (elem: HTMLElement, field: ModelSubfield) => Widget;

/**
 * Base class for all widgets
 */
export abstract class Widget {

	private lastValue: string = "";
	private parentFieldsExpanded: boolean = false;
	protected inputEntryCallbackID: number = 0;

	/** 
	 * the root element of the widget, all widget related elements should 
	 * be contained within this element 
	 */
	public element: HTMLElement = null;
	public parentField: ModelSubfield = null;
	public onEnterValue: SimpleEvent<string> = new SimpleEvent();

	/** holds congfiguration properties for the widget */
	public properties: BaseProperties = {};
	
	public onValueChanged: SimpleEvent = new SimpleEvent();

	/// Initialization ---------------------------------------------------------
	
	public constructor(elem: HTMLElement, parentField: ModelSubfield) {
			this.element = elem;
			this.element.setAttribute(widgetAttribute, (this as any).constructor.name)
			this.parentField = parentField;
			this.properties = this.getDefaultProperties();
	
			// parse all the properties defined in the data property attribute of 
			// the top-level element for the widget and apply them to this class
			const propsJson = elem.getAttribute(propertiesDataValue)
			if(propsJson != undefined) {
				const propsObj = JSON.parse(propsJson)
				for(const prop in propsObj) {
					this.properties[prop] = propsObj[prop];
				}
			}
	}
	
	public setValue(value: string): void{
		this.getInputElement().value = value;
	}

	protected checkForInputElementEventInit(): void {
		const inputElem = this.getInputElement();

		// TODO maybe kinda hacky to use set timeout here but meh
		if(inputElem == null){
			setTimeout(()=>{ this.checkForInputElementEventInit(); }, 1000);
			return;
		}

		const eventStr = inputElem instanceof HTMLSelectElement ? 
			"change" : "input";
		inputElem.addEventListener(eventStr, e => this.onInputChange(e));
	}

	/** set default properties on the widget */
	protected getDefaultProperties(): BaseProperties {
		return {
			requirementLevel: RequirementLevel.OPTIONAL,
		};
	}

	/** collect data from json script elements */
	protected collectData(): void {
		const jsonElem = this.element.querySelector(
			`script[${widgetDataAttribute}=${propertiesDataValue}]`
		);
		if(jsonElem != null) this.properties = JSON.parse(jsonElem.textContent);
	}

	/** custom initialization logic for widget */
	public initialize(): void {
		this.collectData();
		if(this.properties.requirementLevel != undefined) {
			this.element.setAttribute(
				requirementAttributeContainer,
				this.properties.requirementLevel.toString(),
			);
		}

		// TODO maybe kinda hacky to use set timeout here but meh
		setTimeout(() => this.checkForInputElementEventInit());
	}

	/// Restricted functionality -----------------------------------------------

	protected getValueEntryDelay(): number {
		let delay = 50;
		const inputElem = this.getInputElement();
		if(inputElem instanceof HTMLTextAreaElement) delay = 500;
		else if (inputElem instanceof HTMLInputElement){
			if(["text", "email", "url", "password"].includes(inputElem.type)) {
				delay = 500; // milliseconds
			}
		}
		return delay;
	}

	protected triggerValueEntered(): void{
		const inputValue: string = this.getInputValue();
		this.onEnterValue.triggerEvent(inputValue);

		// expand subfields if applicable and its first time a value is entered
		if(this.parentField != null && !this.parentFieldsExpanded) {
			this.parentField.expandSubfields();
			this.parentFieldsExpanded = true;
		}
	}

	protected onInputChange(event: Event): void {

		// cancel previous callback if it exists
		if(this.inputEntryCallbackID > 0){
			clearTimeout(this.inputEntryCallbackID);
			this.inputEntryCallbackID = 0;
		}

		// trigger valueEntered after a delay
		setTimeout(() => {
			this.triggerValueEntered();
			this.inputEntryCallbackID = 0;
		}, this.getValueEntryDelay());

		if(this.parentField) this.parentField.onValueChanged.triggerEvent();
	}

	/// Public functionality ---------------------------------------------------

	/** return the element that the user interacts with for inputing data */
	public abstract getInputElement(): AnyInputElement;

	/** returns the value that a user has input into the widget */
	public getInputValue(): string { return this.getInputElement().value.trim(); }

	public destroy(): void {
		this.element.remove();
	}

	/// Static -----------------------------------------------------------------

	/** map of all registered widgets that are accessible */
	private static registeredWidgets: Map<string, WidgetType> = new Map();

	/**
	 * construct a set of widgets from a given set of elements
	 * @param widgetClass the type of widget to query for
	 * @param elements the elements to create widgets from
	 */
	private static getWidgetsFromElements(
		widgetClass: WidgetType,
		elements: Iterable<Element>,
	): Array<Widget> {

		// iterate through each element and create widget from it
		const widgets: Array<Widget> = []
		for(const element of elements) {
			if(element instanceof HTMLElement){
				const widget = new widgetClass(element, null);
				widgets.push(widget);
			}
		}
		return widgets;
	}

	/**
	 * construct and initialize all widgets of a given type in a webpage
	 * @param widgetClass the widget type to initialize
	 */
	public static initializeWidgets(widgetClass: WidgetType): Array<Widget> {
		console.log("Initializing " + widgetClass.name + " widgets..")
		const widgets = this.getWidgetsFromElements(
			widgetClass, 
			document.querySelectorAll(`[${widgetAttribute}='${widgetClass.name}']`),
		);
		
		for(const widget of widgets) widget.initialize();
		console.log("Initialized " + widgets.length)

		return widgets;
	}

	/** construct and initialize all previously registered widgets in a webpage */
	public static initializeRegisteredWidgets(): void {
		for(const widgetType of this.registeredWidgets.values()) {
			this.initializeWidgets(widgetType);
		}
	}

	/**
	 * Register many widgets types that can be used for dynamic form generation
	 * @example
	 * Widget.registerWidgets(MyWidgetA, MyWidgetB, ...);
	 */
	public static registerWidgets(...widgetClasses: WidgetType[]): void {
		for(const widgetClass of widgetClasses) {
			this.registeredWidgets.set(widgetClass.name, widgetClass);
		}
	}

	/** gets a registered widget type by name, if it exists, otherwise null */
	public static getRegisteredWidget(
		className: string
	): WidgetType {
		if(this.registeredWidgets.has(className)) {
			return this.registeredWidgets.get(className);
		}
		return null;
	}

	public static getAllRegisteredWidgets(): WidgetType[] {
		const widgets: WidgetType[] = [];
		for(const widget of this.registeredWidgets.values()) {
			widgets.push(widget);
		}
		return widgets;
	}
}