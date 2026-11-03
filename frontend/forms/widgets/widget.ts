/**
 * Module that handles definition of base class for all widgets
 *
 * Also defines the widget registry and the `data-hssi-*` attribute names that
 * tie widgets to their HTML elements. Touch this when writing a new widget type
 * or changing how widgets are found and initialized.
 *
 * @module
 */

import { 
	ModelSubfield, requirementAttributeContainer, RequirementLevel, SimpleEvent,
	type JSONObject,
	type JSONValue
} from "../../loader";

// names of values in data attributes
/**
 * `"json-properties"`: the attribute (and JSON `<script>` marker) holding a
 * widget's configuration properties.
 */
export const propertiesDataValue = "json-properties";

// names of attributes on html element that specify widget information
/** `"data-hssi-uid"`: attribute holding a widget element's UID. */
export const uidAttribute = "data-hssi-uid";
/**
 * `"data-hssi-widget"`: attribute naming the widget class an element belongs
 * to.
 */
export const widgetAttribute = "data-hssi-widget";
/**
 * `"data-hssi-data"`: attribute marking a JSON `<script>` element with widget
 * data.
 */
export const widgetDataAttribute = "data-hssi-data";
/** `"data-hssi-type"`: attribute holding a widget element's type. */
export const typeAttribute = "data-hssi-type";

/**
 * Configuration properties shared by all widgets: `requirementLevel`,
 * `maxLength`, `autofillSiblings`. Subclasses extend it with their own.
 */
export interface BaseProperties extends Record<string, any> {
	requirementLevel?: RequirementLevel;
	maxLength?: number;
	autofillSiblings?: boolean;
}

/**
 * An `<input>`, `<textarea>` or `<select>` element, optionally carrying a
 * `data` JSON object.
 */
export type AnyInputElement = (
	HTMLInputElement |
	HTMLTextAreaElement |
	HTMLSelectElement
) & { data?: JSONObject }

/** Constructor type of a widget class: `new (elem, field) => Widget`. */
export type WidgetType = new (elem: HTMLElement, field: ModelSubfield) => Widget;

/** Base class for all widgets */
export abstract class Widget {

	private lastValue: string = "";
	private parentFieldsExpanded: boolean = false;
	/** Timer ID of the pending value-entered callback. */
	protected inputEntryCallbackID: number = 0;

	/** 
	 * the root element of the widget, all widget related elements should 
	 * be contained within this element 
	 */
	public element: HTMLElement = null;
	/** The `ModelSubfield` this widget belongs to, or `null`. */
	public parentField: ModelSubfield = null;
	/**
	 * Fires with the input value once the user stops typing (after the entry
	 * delay).
	 */
	public onEnterValue: SimpleEvent<string> = new SimpleEvent();

	/** holds congfiguration properties for the widget */
	public properties: BaseProperties = {};
	
	/**
	 * Change event for subclasses to fire; the base class never triggers it.
	 */
	public onValueChanged: SimpleEvent = new SimpleEvent();

	/// Initialization ---------------------------------------------------------
	
	/**
	 * Binds the widget to its root element and field, applies default
	 * properties, then any from the element's `json-properties` attribute.
	 */
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

	/**
	 * Attaches input listeners, polling every second until the input element
	 * exists.
	 */
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
	public initialize(readOnly: boolean = false): void {
		this.collectData();
		if(!readOnly && this.properties.requirementLevel != undefined) {
			this.element.setAttribute(
				requirementAttributeContainer,
				this.properties.requirementLevel.toString(),
			);
		}

		// TODO maybe kinda hacky to use set timeout here but meh
		setTimeout(() => this.checkForInputElementEventInit());
	}

	/// Restricted functionality -----------------------------------------------

	/**
	 * Milliseconds to wait after input before treating a value as entered: 500
	 * for text-like inputs, 50 otherwise.
	 */
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

	/**
	 * Fires `onEnterValue` and expands the parent field's subfields the first
	 * time a value is entered.
	 */
	protected triggerValueEntered(): void{
		const inputValue: string = this.getInputValue();
		this.onEnterValue.triggerEvent(inputValue);

		// expand subfields if applicable and its first time a value is entered
		if(this.parentField != null && !this.parentFieldsExpanded) {
			this.parentField.expandSubfields();
			this.parentFieldsExpanded = true;
		}
	}

	/**
	 * Input handler: schedules `triggerValueEntered` after the entry delay and
	 * notifies the parent field.
	 */
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

	/**
	 * Sets the input value, and by default notifies the parent field that it
	 * changed.
	 */
	public setValue(value: string, notify: boolean = true): void{
		this.getInputElement().value = value;
		if(notify && this.parentField) this.parentField.onValueChanged.triggerEvent();
	}

	/** return the element that the user interacts with for inputing data */
	public abstract getInputElement(): AnyInputElement;

	/** returns the value that a user has input into the widget */
	public getInputValue(): string { return this.getInputElement().value.trim(); }

	/** Removes the widget's element from the page. */
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

	/** All registered widget types. */
	public static getAllRegisteredWidgets(): WidgetType[] {
		const widgets: WidgetType[] = [];
		for(const widget of this.registeredWidgets.values()) {
			widgets.push(widget);
		}
		return widgets;
	}
}