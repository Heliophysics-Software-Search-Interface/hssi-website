import { 
    PopupDialogue, RorFinder, UrlWidget, faMagicIcon 
} from "../../loader"

export abstract class FindIdWidget extends UrlWidget { }

export class RorWidget extends FindIdWidget {

    protected findButton: HTMLButtonElement = null;
    
    protected buildFindButton(): void {
        
        this.findButton = document.createElement("button");
        this.findButton.type = "button";
        this.findButton.innerHTML = faMagicIcon + " find";
        this.findButton.addEventListener("click", () => {
            this.onFindPressed();
        });

        this.element.appendChild(this.findButton);
    }
    
    private onFindPressed(): void {
        const rorPopup = RorFinder.getInstance();
        rorPopup.setTarget(this.parentField);
        PopupDialogue.showPopup(rorPopup);
    }

    override initialize(): void {
        super.initialize();
        this.buildFindButton();
    }
}