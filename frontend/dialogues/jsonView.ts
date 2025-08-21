import { 
	type JSONArray, type JSONObject, type JSONValue
} from "../util";

export class JsonView {
	
	public jsonData: JSONObject | JSONArray = null;
	private element: HTMLDivElement = null;

	public constructor(
		data: JSONObject | JSONArray, 
		div: HTMLDivElement = null
	) {
		this.jsonData = data;
		this.element = div;
	}

	private buildElement(): void {
		this.element = document.createElement("div");
		this.forceRebuildDiv();
	}

	private createDivFromObject(json: JSONObject): HTMLDivElement {
		const div = document.createElement("div");
		for(const key in json){
			if(key == "id") continue;
			const val = json[key];
			if(val == "UNKNOWN") continue;
			const field = this.createField(key, val);
			div.appendChild(field);
		}
		return div;
	}

	private createDivsFromArray(json: JSONArray): HTMLDivElement[] {
		const divs: HTMLDivElement[] = [];
		for(const val of json){
			const div = document.createElement("div");
			let elem = this.createField("", val);
			const childs = elem.querySelectorAll("div span");
			if(childs.length == 1){
				elem = childs[0] as any;
			}
			div.appendChild(elem);
			divs.push(div);
		}
		return divs;
	}

	private createField(
		fieldName: string,
		json: JSONValue
	): HTMLElement {
		if(json instanceof Array) {
			const title = document.createElement("summary");			
			title.innerHTML = `<strong>${fieldName}</strong>: `;
			const subfields = this.createDivsFromArray(json);
			const detail = document.createElement("details");
			const body = document.createElement("div");
			for(const sub of subfields) body.appendChild(sub);
			detail.appendChild(title);
			detail.appendChild(body);
			detail.open = true;
			return detail;
		}
		else if (json instanceof Object) {
			const title = document.createElement("summary");
			title.innerHTML = `<strong>${fieldName}</strong> `;
			const body = this.createDivFromObject(json);
			const detail = document.createElement("details");
			detail.appendChild(title);
			detail.appendChild(body);
			detail.open = true;
			return detail;
		}
		else {
			const span = document.createElement("span");
			span.innerHTML = `<strong>${fieldName}</strong> ${json?.toString()}`;
			return span;
		}
	}

	public forceRebuildDiv(): void {

		// remove all children
		while(this.element.childNodes.length > 0){
			this.element.childNodes[0].remove();
		}

		// build structure
		const fieldContainer = this.createField("", this.jsonData);
		this.element.appendChild(fieldContainer);
	}

	public getDiv(): HTMLDivElement {
		if(!this.element) this.buildElement();
		return this.element;
	}

	public static divFromJson(json: JSONObject | JSONArray): HTMLDivElement{
		return new JsonView(json).getDiv();
	}
}

const win = window as any;
win.divFromJson = JsonView.divFromJson.bind(JsonView);