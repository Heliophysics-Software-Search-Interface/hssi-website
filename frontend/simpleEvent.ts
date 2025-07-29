/**
 * T - input type for listeners
 * R - return type for listeners
 */
export class SimpleEvent<T = undefined, R = void>{

	/** 
	 * if true, new listeners that are added will be fired if the event has been 
	 * triggered before, passing the most recently used parameter as an argument
	 */
	public refireNewListeners: boolean = false;

	/** the listener functions that will be fired when the event is triggered */
	public listeners: Array<(arg: T) => R> = [];

	/** the last parameter the event was triggered with */
	private _lastParam: T = undefined;

	public constructor(){ }

	/**
	 * add an event listener to the event that will fire when the event is 
	 * triggered
	 * @param listener 
	 */
	public addListener(listener: (args: T) => R): (args: T) => R{
		this.listeners.push(listener)

		// refire new listeners if applicable
		if (this.refireNewListeners && this._lastParam !== undefined) {
			listener(this._lastParam);
		}

		return listener;
	}

	/**
	 * removes the specified listener from the event so it will no longer be
	 * called when the event is triggered
	 * @param listener 
	 */
	public removeListener(listener: (args: T) => R): void {
		const index = this.listeners.indexOf(listener);
		if(index >= 0) this.listeners.splice(index, 1);
	}

	/**
	 * remove all listeners from the event so nothing happens when the event is
	 * triggered
	 */
	public clearListeners(): void{
		this.listeners.splice(0, this.listeners.length);
	}

	/** 
	 * fire off all the listeners with the specified parameter and returns an 
	 * array of all the results from each event call
	 * @param argument the argument that will be passed to the listeners
	 */
	public triggerEvent(argument: T = undefined): Array<R>{

		const val: Array<R> = []

		for(const listener of this.listeners){
			val.push(listener(argument));
		}

		// cache last argument
		if (argument === undefined) argument = true as any;
		else this._lastParam = argument;

		return val;
	}
}