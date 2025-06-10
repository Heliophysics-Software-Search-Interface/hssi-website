const styleSpinnerPopup = "hssi-spinner-popup";
const styleSpinnerBackdrop = "hssi-spinner-backdrop";
const faSpinner = "<i class='fa fa-spinner fa-spin'></i>";

export class Spinner {

    private backdropElement: HTMLDivElement;
    private popupElement: HTMLDivElement;
    private messageElement: HTMLParagraphElement;
    private pervasiveness: number = 0;

    private constructor() {

        this.backdropElement = document.createElement("div");
        this.backdropElement.classList.add(styleSpinnerBackdrop);
        this.backdropElement.style.position = "fixed";
        this.backdropElement.style.top = "0";
        this.backdropElement.style.left = "0";
        this.backdropElement.style.width = "100vw";
        this.backdropElement.style.height = "100vh";
        this.backdropElement.style.zIndex = "100000";

        this.popupElement = document.createElement("div");
        this.popupElement.classList.add(styleSpinnerPopup);
        this.popupElement.style.position = "absolute";
        this.popupElement.style.width = "400px";
        this.popupElement.style.zIndex = "100001";
        this.popupElement.innerHTML = "<h5>" + faSpinner + " Please wait...</h3>";
        this.messageElement = document.createElement("p");

        this.popupElement.appendChild(this.messageElement);
        document.body.appendChild(this.backdropElement);
        document.body.appendChild(this.popupElement);
    }

    private show(): void {
        this.pervasiveness += 1;
        if (this.pervasiveness >= 1) {
            this.backdropElement.style.display = "block";
            this.popupElement.style.display = "block";
        }
    }

    private hide(): void {
        this.pervasiveness -= 1;
        if (this.pervasiveness <= 0) {
            this.pervasiveness = 0;
            this.backdropElement.style.display = "none";
            this.popupElement.style.display = "none";
        }
    }

    private centerPopup(): void {
        this.popupElement.style.top = (
            `${window.innerHeight / 2 - this.popupElement.offsetHeight / 2 + window.scrollY}px`
        );
        this.popupElement.style.left = (
            `${window.innerWidth / 2 - this.popupElement.offsetWidth / 2 + window.scrollX}px`
        );
    }

    /// Static -----------------------------------------------------------------

    private static instance: Spinner = null;

    private static validateInstance(): void {
        if (this.instance === null) {
            this.instance = new Spinner();
        }
    }

    public static showSpinner(message: string = ""): void {
        this.validateInstance();
        this.instance.messageElement.textContent = message;
        this.instance.show();
        this.instance.centerPopup();
    }

    public static hideSpinner(): void {
        this.validateInstance();
        this.instance.hide();
    }
}