import { 
	OrcidFinder, PopupDialogue, RorFinder, DoiDataciteFinder, 
	UrlWidget, faMagicIcon,
	propResultFilters
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
		const rorPopup = RorFinder.getInstance()
			.setTarget(this.parentField)
			.withFilters(this.properties[propResultFilters]);
		PopupDialogue.showPopup(rorPopup);
	}
}

export class OrcidWidget extends FindIdWidget {
	protected override onFindButtonPressed(): void {
		const orcidPopup = OrcidFinder.getInstance()
			.setTarget(this.parentField)
			.withFilters(this.properties[propResultFilters]);
		PopupDialogue.showPopup(orcidPopup);
	}
}

export class DataciteDoiWidget extends FindIdWidget {
	protected override onFindButtonPressed(): void {
		const popup = DoiDataciteFinder.getInstance()
			.setTarget(this.parentField)
			.withFilters(this.properties[propResultFilters]);
		PopupDialogue.showPopup(popup);
	}
}