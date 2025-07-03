export const stylePopupBackdrop = "hssi-spinner-backdrop";
const styleSpinnerPopup = "hssi-spinner-popup";
const faSpinner = "<i class='fa fa-spinner fa-spin'></i>";

export class Spinner {

    private targetElement: HTMLElement = null;
    private backdropElement: HTMLDivElement = null;
    private popupElement: HTMLDivElement = null;
    private messageElement: HTMLParagraphElement = null;
    private pervasiveness: number = 0;

    private constructor() {

        this.backdropElement = document.createElement("div");
        this.backdropElement.classList.add(stylePopupBackdrop);
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
            this.backdropElement.style.position = (
                this.targetElement ? "absolute" : "fixed"
            );
            this.popupElement.style.display = "block";
            this.positionBackdrop();
            this.centerPopup();
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

    private destroy(): void {
        this.backdropElement.remove();
        this.popupElement.remove();
        this.targetElement = null;
        this.pervasiveness = 0;
        if(this.targetElement && Spinner.spinnerMap.has(this.targetElement)){
            Spinner.spinnerMap.delete(this.targetElement);
        }
    }

    private centerPopup(): void {
        if(this.targetElement){
            const targRect = this.targetElement.getBoundingClientRect();

            const posY = targRect.top + window.scrollY + targRect.height / 2;
            const offY = this.popupElement.offsetHeight / 2;
            this.popupElement.style.top = `${posY - offY}px`;
            
            const posX = targRect.left + window.scrollX + targRect.width / 2;
            const offX = this.popupElement.offsetWidth / 2;
            this.popupElement.style.left = `${posX - offX}px`;
        }
        else{
            this.popupElement.style.top = (
                `${window.innerHeight / 2 - this.popupElement.offsetHeight / 2 + window.scrollY}px`
            );
            this.popupElement.style.left = (
                `${window.innerWidth / 2 - this.popupElement.offsetWidth / 2 + window.scrollX}px`
            );
        }
    }

    private positionBackdrop(): void {
        if(this.targetElement) {
            const rect = this.targetElement.getBoundingClientRect();
            this.backdropElement.style.top = `${rect.top + window.scrollY}px`;
            this.backdropElement.style.left = `${rect.left + window.scrollX}px`;
            this.backdropElement.style.width = `${rect.width}px`;
            this.backdropElement.style.height = `${rect.height}px`;
        }
        else{
            this.backdropElement.style.top = "0";
            this.backdropElement.style.left = "0";
            this.backdropElement.style.width = "100vw";
            this.backdropElement.style.height = "100vh";
        }
    }

    /// Static -----------------------------------------------------------------

    private static instance: Spinner = null;

    private static spinnerMap: Map<HTMLElement, Spinner> = new Map();

    private static updateSpinners(): void {
        let count = 0;
        for(const key of this.spinnerMap.keys()){
            const spinner = this.spinnerMap.get(key);
            if(!document.body.contains(key)){
                spinner.destroy();
                continue;
            }
            spinner.positionBackdrop();
            spinner.centerPopup();
            count += 1;
        }

        // update spinners continuously as long as there are any left
        if(count > 0){
            setTimeout(() => {
                this.updateSpinners();
            }, 0);
        }
    }

    private static validateInstance(): void {
        if (this.instance === null) {
            this.instance = new Spinner();
        }
    }

    private static createTargetedSpinner(target: HTMLElement): Spinner {
        const spinner = new Spinner();
        spinner.targetElement = target;
        const zIndex = Number.parseInt(window.getComputedStyle(target).zIndex) || 100000;
        console.log(window.getComputedStyle(target));
        spinner.backdropElement.style.zIndex = (zIndex + 100).toString();
        spinner.backdropElement.classList.add("targeted");
        spinner.popupElement.style.zIndex = (zIndex + 101).toString();
        spinner.popupElement.classList.add("targeted");
        return spinner;
    }

    public static showSpinner(message: string = "", target: HTMLElement = null): void {
        if(target == null) {
            this.validateInstance();
            this.instance.messageElement.textContent = message;
            this.instance.show();
            this.instance.centerPopup();
            return;
        }

        // create a spinner targeted over one html element
        this.hideSpinner(target);
        const spinner = this.createTargetedSpinner(target);
        console.log(spinner);
        this.spinnerMap.set(target, spinner);
        spinner.show();
        this.updateSpinners();
    }

    public static hideSpinner(target: HTMLElement = null): void {
        if(target == null) {
            this.validateInstance();
            this.instance.hide();
            return;
        }
        this.spinnerMap.get(target)?.destroy();
    }
}