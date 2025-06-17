import { 
    OrcidFinder, PopupDialogue, RorFinder, UrlWidget, faMagicIcon 
} from "../../loader"

export abstract class FindIdWidget extends UrlWidget {

    protected findButton: HTMLButtonElement = null;
    protected get findButtonText(): string { return "find"; }

    protected abstract onFindButtonPressed(): void;

    protected buildFindButton(): void {
        
        this.findButton = document.createElement("button");
        this.findButton.type = "button";
        this.findButton.innerHTML = faMagicIcon + " " + this.findButtonText;
        this.findButton.addEventListener("click", () => {
            this.onFindButtonPressed();
        });

        this.element.appendChild(this.findButton);
    }

    override initialize(): void {
        super.initialize();
        this.buildFindButton();
    }
}

export class RorWidget extends FindIdWidget {
    protected override onFindButtonPressed(): void {
        const rorPopup = RorFinder.getInstance();
        rorPopup.setTarget(this.parentField);
        PopupDialogue.showPopup(rorPopup);
    }
}

export class OrcidWidget extends FindIdWidget {
    protected override onFindButtonPressed(): void {
        const orcidPopup = OrcidFinder.getInstance();
        orcidPopup
    }
}