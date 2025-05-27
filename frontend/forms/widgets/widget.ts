/**
 * Module that handles definition of base class for all widgets
 */

import { FieldRequirement, requirementAttribute, requirementAttributeContainer, RequirementLevel } from "../../loader";

// names of values in data attributes
export const propertiesDataValue = "json-properties";

// names of attributes on html element that specify widget information
export const uidAttribute = "data-hssi-uid";
export const widgetAttribute = "data-hssi-widget";
export const widgetDataAttribute = "data-hssi-data";
export const typeAttribute = "data-hssi-type";
export const targetUuidAttribute = "data-hssi-target-uuid";

export interface BaseProperties extends Record<string, any> {
	requirement_level: RequirementLevel;
}

type WidgetType = new (elem: HTMLElement) => Widget;

/**
 * Base class for all widgets
 */
export abstract class Widget {

	/** 
	 * the root element of the widget, all widget related elements should 
	 * be contained within this element 
	 */
	public element: HTMLElement | null = null;

	/** holds congfiguration properties for the widget */
	public properties: BaseProperties = {} as any;

	public constructor(elem: HTMLElement) {
		this.element = elem;
		this.properties = this.getDefaultProperties()

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

	/** set default properties on the widget */
	protected getDefaultProperties(): BaseProperties {
		return {
			requirement_level: RequirementLevel.OPTIONAL,
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
				this.properties.requirementLevel
			);
		}
	}

	/** return the element that the user interacts with for inputing data */
	public abstract getInputElement(): HTMLInputElement;

	/** get the requiredinput object associated with the widget */
	public getRequiredInputInstance(): FieldRequirement {
		return FieldRequirement.getFromElement(this.element);
	}

	/** map of all registered widgets that are accessible */
	private static registeredWidgets: Map<
		string, new (elem: HTMLElement) => Widget
	> = new Map();

	/**
	 * construct a set of widgets from a given set of elements
	 * @param widgetClass the type of widget to query for
	 * @param elements the elements to create widgets from
	 */
	private static getWidgetsFromElements(
		widgetClass: new (elem: HTMLElement) => Widget,
		elements: Iterable<Element>,
	): Array<Widget> {

		// iterate through each element and create widget from it
		const widgets: Array<Widget> = []
		for(const element of elements) {
			if(element instanceof HTMLElement){
				const widget = new widgetClass(element);
				widgets.push(widget);
			}
		}
		return widgets;
	}

	/**
	 * construct and initialize all widgets of a given type in a webpage
	 * @param widgetClass the widget type to initialize
	 */
	public static initializeWidgets(
		widgetClass: new (elem: HTMLElement) => Widget,
	): Array<Widget> {
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