import { Widget, type AnyInputElement } from "../../loader";

export abstract class InputWidget extends Widget {

    protected inputElement: HTMLInputElement;

    protected abstract getInputType(): string;

    protected createElements(): void {
        this.inputElement = document.createElement("input") as any;
        this.inputElement.type = this.getInputType();
        this.element.appendChild(this.inputElement);
    }

    public initialize(): void {
        super.initialize();
        this.createElements();
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

    protected createElements(): void {
        this.textAreaElement = document.createElement("textarea") as any;
        this.element.appendChild(this.textAreaElement);
    }

    public initialize(): void {
        super.initialize();
        this.createElements();
    }

    public getInputElement(): AnyInputElement { return this.textAreaElement; }
}