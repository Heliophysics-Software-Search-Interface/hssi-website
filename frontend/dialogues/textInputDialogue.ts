import { 
	PopupDialogue 
} from "../loader";

export class TextInputDialogue extends PopupDialogue {

	private messageElement: HTMLDivElement = null;
	private inputElement: HTMLInputElement = null;
	private buttonElement: HTMLButtonElement = null;

	protected override createContent(): void {
		super.createContent();
		
		this.messageElement = document.createElement("div");
		this.inputElement = document.createElement("input");
		this.buttonElement = document.createElement("button");
		this.buttonElement.type = "button";
		this.inputElement.type = "text";

		this.contentElement.appendChild(this.messageElement);
		this.contentElement.appendChild(this.inputElement);
		this.contentElement.appendChild(this.buttonElement);
	}

	public static instance: TextInputDialogue = null;

	public static validateInstance(): void {
		if(this.instance != null) return;
		this.instance = new TextInputDialogue();
	}

	/**
	 * prompt the user for text input and return the string when they enter it
	 * @param message the message to show to the user
	 * @param buttonText the text to appear on the button to confirm text input
	 */
	public static async promptInput(message: string, buttonText: string = "accept"): Promise<string> {
		this.validateInstance();
		this.instance.messageElement.innerText = message;
		this.instance.buttonElement.innerText = buttonText;
		this.instance.inputElement.value = "";
		PopupDialogue.showPopup(this.instance);

		const checkForClosedDialogue = (accept: ()=>any, cancel: ()=>any) => {
			if(!PopupDialogue.popupIsShown()) {
				this.instance.buttonElement.removeEventListener("click", accept);
				cancel();
			}
			else setTimeout(() => { 
				checkForClosedDialogue(accept, cancel); 
			}, 100);
		};

		PopupDialogue.showPopup(this.instance);
		this.instance.inputElement.focus();
		return new Promise(resolve => {
			const accept = () => {
				PopupDialogue.hidePopup();
				this.instance.inputElement.removeEventListener("keypress", enterCheck);
				resolve(this.instance.inputElement.value);
			};
			const cancel = () => { 
				PopupDialogue.hidePopup();
				this.instance.inputElement.removeEventListener("keypress", enterCheck);
				resolve(null);
			};
			const enterCheck = (e: KeyboardEvent) => {
				if(e.key == "Enter"){
					accept();
					this.instance.inputElement.removeEventListener("keypress", enterCheck);
				}
			}
			this.instance.buttonElement.addEventListener(
				"click", accept, { once: true }
			);
			this.instance.inputElement.addEventListener("keypress", enterCheck);
			checkForClosedDialogue(accept, cancel);
		});
	}
}