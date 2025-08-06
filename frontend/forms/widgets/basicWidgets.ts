import { Widget, type AnyInputElement } from "../../loader";

export abstract class InputWidget extends Widget {

	protected inputElement: HTMLInputElement;

	protected abstract getInputType(): string;

	protected createElements(): void {
		this.inputElement = document.createElement("input") as any;
		this.inputElement.type = this.getInputType();
		this.element.appendChild(this.inputElement);
		
		const maxLength = this.properties?.maxLength ?? 100;
		this.inputElement.setAttribute("maxlength", maxLength.toString());
	}

	public initialize(readOnly: boolean = false): void {
		super.initialize(readOnly);
		this.createElements();
		this.inputElement.readOnly = readOnly;
	}

	public getInputElement(): HTMLInputElement { return this.inputElement; }
}

export class CharWidget extends InputWidget {
	protected getInputType(): string { return "text"; }
}

export class NumberWidget extends InputWidget{
	protected getInputType(): string { return "number"; }
}

export class UrlWidget extends InputWidget {
	protected getInputType(): string { return "url"; }
}

export class EmailWidget extends InputWidget {
	protected getInputType(): string { return "email"; }
}

export class DateWidget extends InputWidget {
	protected getInputType(): string { return "date"; }
}

export class CheckboxWidget extends InputWidget {
	protected getInputType(): string { return "checkbox"; }
}

export class TextAreaWidget extends Widget {
	protected textAreaElement: HTMLInputElement;

	protected createElements(readOnly: boolean): void {
		this.textAreaElement = document.createElement("textarea") as any;
		this.textAreaElement.readOnly = readOnly;
		this.element.appendChild(this.textAreaElement);
		if(this.properties.maxLength != null){
			this.textAreaElement.setAttribute(
				"maxlength",
				this.properties.maxLength.toString()
			);
		}
	}

	public initialize(readOnly: boolean = false): void {
		super.initialize(readOnly);
		this.createElements(readOnly);
	}

	public getInputElement(): AnyInputElement { return this.textAreaElement; }
}