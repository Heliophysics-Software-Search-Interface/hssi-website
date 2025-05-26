import { Widget } from "../../loader";

abstract class InputWidget extends Widget {

    protected inputElement: HTMLInputElement;

    protected abstract getInputType(): string;

    protected createElements(): void {
        this.inputElement = document.createElement("input") as any;
        this.inputElement.type = this.getInputType();
        this.element.appendChild(this.inputElement);
    }

    protected initialize(): void {
        super.initialize();
        this.createElements();
    }

    public getInputElement(): HTMLInputElement { return this.inputElement; }
}

export class CharWidget extends InputWidget {
    protected getInputType(): string { return "text"; }
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

    protected initialize(): void {
        super.initialize();
        this.createElements();
    }

    public getInputElement(): HTMLInputElement { return this.textAreaElement; }
}