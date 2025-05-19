/**
 * Module that handles definition of base class for all widgets
 */

/** 
 * name of the attribute on the html element that contains JSON properties 
 * for widget configuration 
 */
export const propertiesType = "json-properties";
export const uidAttribute = "data-hssi-uid";

/** name of attribute on html element that specifies the wudget type */
export const widgetAttribute = "data-hssi-widget";
export const typeAttribute = "data-hssi-type";

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
	public properties: Record<string, any> = {};

	public constructor(elem: HTMLElement) {
		this.element = elem;
		this.setDefaultProperties()

		// parse all the properties defined in the data property attribute of 
		// the top-level element for the widget and apply them to this class
		const propsJson = elem.getAttribute(propertiesType)
		if(propsJson != undefined) {
			const propsObj = JSON.parse(propsJson)
			for(const prop in propsObj) {
				this.properties[prop] = propsObj[prop];
			}
		}
	}

	/** set default properties on the widget */
	protected abstract setDefaultProperties(): void

	/** custom initialization logic for widget */
	protected abstract initialize(): void

	/**
	 * construct a set of widgets from a given set of elements
	 * @param widgetClass the type of widget to query for
	 * @param elements the elements to create widgets from
	 */
	private static getWidgetsFromElements<WidgetClass extends Widget>(
		widgetClass: new (elem: HTMLElement) => WidgetClass,
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
	public static initializeWidgets<WidgetClass extends Widget>(
		widgetClass: new (elem: HTMLElement) => WidgetClass,
	): Array<Widget> {
		console.log("Initializing " + widgetClass.name + " widgets..")
		const widgets = this.getWidgetsFromElements(
			widgetClass, 
			document.querySelectorAll(`[${widgetAttribute}='${widgetClass.name}']`),
		);
		console.log("found " + widgets.length + " with " + `[${widgetAttribute}='${widgetClass.name}']`)
		for(const widget of widgets) widget.initialize();
		return widgets;
	}
}