import { PopupDialogue } from "../loader";

export class ConfirmDialogue extends PopupDialogue {

	private messageElement: HTMLDivElement = null;
	private acceptElement: HTMLButtonElement = null;
	private cancelElement: HTMLButtonElement = null;

	protected override createContent(): void {
		super.createContent();
		
		this.messageElement = document.createElement("div");
		this.acceptElement = document.createElement("button");
		this.cancelElement = document.createElement("button");

		this.contentElement.appendChild(this.messageElement);
		this.contentElement.appendChild(this.acceptElement);
		this.contentElement.appendChild(this.cancelElement);
	}

	/// Static -----------------------------------------------------------------

	private static instance: ConfirmDialogue = null;

	public static validateInstance(): void {
		if(this.instance != null) return;
		this.instance = new ConfirmDialogue();
	}

	public static async getConfirmation(
		message: string = "Are you sure?",
		title: string = "Confirm",
		acceptText: string = "accept",
		cancelText: string = "cancel",
	): Promise<boolean> {
		if(PopupDialogue.popupIsShown()){
			console.error(
				"Confirm dialoge cannot be shown since" +
				" there is already a popup visible"
			);
			return false;
		}
		this.validateInstance();
		
		this.instance.titleElement.innerText = title;
		this.instance.messageElement.innerText = message;
		this.instance.acceptElement.innerText = acceptText;
		if(cancelText != null){
			this.instance.cancelElement.innerText = cancelText;
			this.instance.cancelElement.style.display = "inline-block";
		}
		else {
			this.instance.cancelElement.style.display = "none";
		}
		
		const checkForClosedDialogue = (accept: ()=>any, cancel: ()=>any) => {
			if(!PopupDialogue.popupIsShown()) {
				this.instance.acceptElement.removeEventListener("click", accept);
				this.instance.cancelElement.removeEventListener("click", cancel);
				cancel();
			}
			else setTimeout(() => { 
				checkForClosedDialogue(accept, cancel); 
			}, 100);
		};

		PopupDialogue.showPopup(this.instance);
		return new Promise(resolve => {
			const accept = () => {
				PopupDialogue.hidePopup();
				this.instance.cancelElement.removeEventListener("click", cancel);
				resolve(true); 
			};
			const cancel = () => { 
				PopupDialogue.hidePopup();
				this.instance.acceptElement.removeEventListener("click", accept);
				resolve(false);
			};
			this.instance.acceptElement.addEventListener(
				"click", accept, { once: true }
			);
			this.instance.cancelElement.addEventListener(
				"click", cancel, { once: true }
			);
			checkForClosedDialogue(accept, cancel);
		});
	}
}