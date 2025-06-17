import { 
    stylePopupBackdrop, faCloseIcon, SimpleEvent,
} from "../loader";

export const stylePopupDialogue = "hssi-popup-dialogue";
export const stylePopupHeader = "hssi-popup-header";
export const stylePopupTitle = "hssi-popup-title";
export const stylePopupContent = "hssi-popup-content";

export class PopupDialogue {

    protected element: HTMLDivElement = null;
    protected headerElement: HTMLDivElement = null;
    protected titleElement: HTMLElement = null;
    protected contentElement: HTMLDivElement = null;

    protected onShow: SimpleEvent = new SimpleEvent();
    protected onHide: SimpleEvent = new SimpleEvent();

    protected get title(): string {
        return "Popup Dialogue";
    }

    protected constructor() {
        setTimeout(() => {
            this.createElement();
            this.createHeader();
            this.createContent();
        }, 0);
    }

    protected createElement(): void {
        this.element = document.createElement("div");
        this.element.classList.add(stylePopupDialogue);
        this.element.style.position = "absolute";
        this.element.style.zIndex = "100001";
        this.element.style.display = "none";
        document.body.appendChild(this.element);
    }

    protected createHeader(): void {
        this.titleElement = document.createElement("span");
        this.titleElement.classList.add(stylePopupTitle);
        this.titleElement.innerText = this.title;

        const buttonClose = document.createElement("button");
        buttonClose.type = "button";
        buttonClose.innerHTML = faCloseIcon;
        buttonClose.style.position = "absolute";
        buttonClose.style.right = "5px";
        buttonClose.style.top = "5px";
        buttonClose.addEventListener("click", () => {
            PopupDialogue.hidePopup();
        });

        const header = document.createElement("div");
        header.classList.add(stylePopupHeader);
        header.style.display = "flex";
        header.style.justifyContent = "center";
        header.style.alignItems = "center";
        header.style.position = "relative";
        this.headerElement = header;

        header.appendChild(this.titleElement);
        header.appendChild(buttonClose);
        this.element.appendChild(header);
    }

    protected createContent(): void {
        const content = document.createElement("div");
        content.classList.add(stylePopupContent);
        this.contentElement = content;
        this.element.appendChild(content);
    }

    public centerPopup(): void {
        if(this.element == null) return;

        this.centerPopupHorizontally();
        const adjustedHeight = window.innerHeight - this.element.offsetHeight;
        this.element.style.top = `${adjustedHeight / 2 + window.scrollY}px`;
    }
    
    public centerPopupHorizontally(): void {
        if(this.element == null) return;
        const adjustedWidth = window.innerWidth - this.element.offsetWidth;
        this.element.style.left = `${adjustedWidth / 2 + window.scrollX}px`;
    }

    /// Static -----------------------------------------------------------------

    private static backdropElement: HTMLDivElement = null;
    private static currentPopup: PopupDialogue = null;

    private static getBackdrop(): HTMLDivElement {
        if(!this.backdropElement) {
            this.backdropElement = document.createElement("div");
            this.backdropElement.classList.add(stylePopupBackdrop);
            this.backdropElement.style.position = "fixed";
            this.backdropElement.style.left = "0";
            this.backdropElement.style.top = "0";
            this.backdropElement.style.width = "100vw";
            this.backdropElement.style.height = "100vh";
            this.backdropElement.style.zIndex = "100000";
            this.backdropElement.style.display = "none";
            document.body.appendChild(this.backdropElement);
            this.backdropElement.addEventListener("click", () => {
                    this.hidePopup();
            });
        }
        return this.backdropElement;
    };

    private static showBackdrop(): void {
        const backdrop = this.getBackdrop();
        backdrop.style.display = "block";
    }

    public static showPopup(popup: PopupDialogue): void {
        if(this.currentPopup) {
            this.hidePopup();
        }
        this.showBackdrop();
        popup.onShow.triggerEvent();
        this.currentPopup = popup;
        this.currentPopup.element.style.display = "block";
        this.currentPopup.centerPopup();
    }

    public static hidePopup(): void {
        if(this.currentPopup) {
            this.currentPopup.element.style.display = "none";
            this.currentPopup.onHide.triggerEvent();
            this.currentPopup = null;
        }
        this.getBackdrop().style.display = "none";
    }
}

(window as any).PopupDialogue = PopupDialogue;