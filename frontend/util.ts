import { ConfirmDialogue, FormGenerator, PopupDialogue, TextInputDialogue } from "./loader";

export const uuid4Regex = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
export const softwareApiUrl = "/api/models/Software/rows/";
export const modelApiUrl = "/api/view/"
export const editApiUrl = "/sapi/software_edit_data/";
export const requestEditUrl = "/request_edit/";
export const csrfTokenName = "csrf-token";

export type JSONValue = string | number | boolean | null | JSONObject | JSONArray | any;
export interface JSONObject { [key: string]: JSONValue }
export interface JSONArray<T = JSONValue> extends Array<T> { }
export interface JSONArrayData extends JSONObject {
	data: JSONArray,
}

/** like 'keyof' but recursively includes keys of nested types */
export type NestedKeys<T, Prefix extends string = ""> = {
	[K in keyof T]: T[K] extends object
	? T[K] extends Function
	? `${Prefix}${K & string}`
	: `${Prefix}${K & string}` | NestedKeys<T[K], "">
	: `${Prefix}${K & string}`;
}[keyof T];

export function getCsrfTokenValue(): string {
	return (
		document.head.querySelector(`meta[name=${csrfTokenName}]`) as any
	).content as string;
}

/**
 * merge two objects together, recursively
 * @param target merge into this object
 * @param source values from this object will overwrite target values
 * @param inPlace if true, nothing will be cloned, so inputs may be modified
 */
export function deepMerge(target: any, source: any, inPlace: boolean = false): any {

	// If either is not an object (or is null), return a clone of source
	if (
		typeof target !== 'object' || typeof source !== 'object' ||
		!target || !source
	)
		return inPlace ? source : structuredClone(source);

	// Clone the target to avoid mutating the original
	const result: any = inPlace ? target : structuredClone(target);

	// Iterate through all keys in the source object
	for (const key of Object.keys(source)) {

		// If both target and source have the same key and both values are 
		// objects, merge recursively
		if (
			key in result &&
			typeof result[key] === 'object' &&
			typeof source[key] === 'object'
		) {
			result[key] = deepMerge(result[key], source[key], inPlace);
		} else {
			// Otherwise, overwrite with a clone of the source value
			result[key] = inPlace ? source[key] : structuredClone(source[key]);
		}
	}

	return result;
}

/**
 * Allow to send a fetch request which aborts if it takes any longer than
 * the specified timeout time
 * @param input @see fetch
 * @param init @see fetch
 * @param timeout in seconds, request will be aborted if it takes longer than this
 */
export async function fetchTimeout(
	input: RequestInfo | URL,
	init: RequestInit = {},
	timeout: number = 10
): Promise<Response> {
	const controller = new AbortController();
	const reqInit = deepMerge(
		init as JSONObject,
		{ signal: controller.signal },
		true
	);
	const timeoutId = setTimeout(() => controller.abort(), timeout * 1000);
	const result = await fetch(input, reqInit);
	clearTimeout(timeoutId);
	return result;
}

/** extract the doi from an identifier URL */
export function extractDoi(url: string): string {
	const split = url.split("doi.org/");
	if (split.length > 1) return split.at(-1);
	return url;
}

/** extract an orcid id from an identifier URL */
export function extractOrcId(url: string): string {
	const split = url.split("orcid.org/");
	if (split.length > 1) return split.at(-1);
	return url;
}

/**
 * get a similarity score of how similar two strings are from 0 to 1, where 0
 * means completely different strings, and 1 means they are the exact same
 */
export function getStringSimilarity(a: string, b: string): number {
	const m = a.length, n = b.length;
	const dp = Array.from({ length: m + 1 }, (_, i) =>
		Array.from({ length: n + 1 }, (_, j) => i === 0 ? j : j === 0 ? i : 0)
	);

	for (let i = 1; i <= m; i++) {
		for (let j = 1; j <= n; j++) {
			if (a[i - 1] === b[j - 1]) {
				dp[i][j] = dp[i - 1][j - 1];
			} else {
				dp[i][j] = 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
			}
		}
	}

	const dist = dp[m][n];
	return 1 - dist / Math.max(m, n); // similarity score
}

/** fetch the software data from the submission with the given uid */
export async function getSoftwareData(uid: string): Promise<JSONObject> {
	const url = softwareApiUrl + uid;
	console.log(`fetching software data at ${url}`);
	const result = await fetchTimeout(url);
	const data = await result.json();
	return data;
}

/** 
 * fetch the software data from the submission with the given uid, uses secure
 * api to fetch from secret url with slightly elevated priveleges to get 
 * submitter data
 */
export async function getEditData(uid: string): Promise<JSONObject> {
	const url = editApiUrl + uid;
	console.log(`fetching edit data at ${url}`);
	const result = await fetchTimeout(url);
	const data = await result.json();
	console.log("recieve edit data", data)
	return data;
}

/** 
 * gets the software data from the proper database table and formats it to be 
 * compatible with the { @see FormGenerator.fillForm } method
 */
export async function getSoftwareFormData(uid: string): Promise<JSONObject> {
	const data = await getSoftwareData(uid);
	console.log("fetched software data: ", data);
	return data;
}

/** 
 * gets the software data from the proper database table and formats it to be 
 * compatible with the { @see FormGenerator.fillForm } method. This is meant 
 * for use with edit form page, as it will have slightly elevated priveleges to
 * fetch submitter data if a valid hit for the secret url is found
 */
export async function getSoftwareEditFormData(uid: string): Promise<JSONObject> {
	const data = await getEditData(uid);
	if(!data.submitter){
		const submitter: JSONObject = (
			data.submissionInfo as JSONObject
		)?.submitter as JSONObject;

		// create a submitter object that matches the fill form data for the
		// fill form function on the form generator, given the submission info
		if(submitter) {
			submitter.submitterName = (
				(submitter.person as JSONObject)?.firstName as string + " " +
				(submitter.person as JSONObject)?.lastName as string
			);
			let emails = JSON.parse((submitter.email as string).replaceAll("'", '"'));
			if(!(emails instanceof Array)) emails = [emails];
			submitter.submitterEmail = emails;
			data.submitterName = submitter;
		}
	}
	console.log("fetched software data: ", data);
	return data;
}

/** gets the api view json data of the specified software submission */
export async function getSimpleSoftwareFormData(uid: string): Promise<JSONObject> {
	const url = modelApiUrl + uid;
	console.log(`fetching software data at ${url}`);
	const result = await fetchTimeout(url);
	const data = await result.json();
	return data;
}

/** 
 * request an email be sent to the software submission with the specified uid,
 * prompting the user to enter an email to confirm they were the submitter 
 */
export async function requestEditSubmission(uid: string): Promise<void> {
	const email = (
		await TextInputDialogue.promptInput(
			"Please enter the email associated with the software submission."
		))?.trim();
	if(email == null) return;

	if(email.length <= 0){
		PopupDialogue.hidePopup();
		ConfirmDialogue.getConfirmation(
			"Invalid email", "Error", "ok", null
		);
		return;
	}

	const url = requestEditUrl + uid;
	const promise = fetchTimeout(url, {
		method: "POST",
		headers: { 
			"Content-Type": "text/plain",
			"X-CSRFToken": getCsrfTokenValue(),
		},
		body: email,
	});

	promise.then(async response => {
		PopupDialogue.hidePopup();
		if(response.ok){
			ConfirmDialogue.getConfirmation(
				"An email with a secure link that will allow you to edit " + 
				"the submission was sent to the email " + 
				"associated with the submission. " +
				"Please make sure to check your junk folder.", 
				"Email Sent", "ok", null
			);
		} else {
			ConfirmDialogue.getConfirmation(
				await response.text(), 
				"Error", "ok", null
			);
		}
	});
	promise.catch(e => {
		PopupDialogue.hidePopup();
		ConfirmDialogue.getConfirmation(String(e), "Error", "ok", null);
	});
}

/**
 * tests a given string to see if it matches the uuid v4 format
 * @param uid the string to test if its a uuid
 */
export function isUuid4(uid: string): boolean {
	return uuid4Regex.test(uid);
}

/** append an async child to a parent element when the child is resolved */
export function appendPromisedElement(parentElem: HTMLElement, childPromise: Promise<HTMLElement>){
	childPromise
		.then(x => parentElem.appendChild(x))
		.catch(e => console.error(e));
}

async function curateEditFormInit() {
	let uid = new URLSearchParams(window.location.search).get("uid");
	
	let data = null;
	try{
		// defined in /frontend/util.ts
		data = await getSoftwareEditFormData(uid);
	}
	catch(e) { console.error(e); }
	
	if(data == null) {
		await ConfirmDialogue.getConfirmation(
			"This edit link is invalid.", "Error", "Ok", null
		);
		window.location.href = "/";
		return;
	}
	
	// defined in /frontend/forms/formGenerator.ts
	await FormGenerator.awaitFormGeneration();
	FormGenerator.fillForm(data, true);
}

const win = window as any;
win.requestEditSubmission = requestEditSubmission;
win.getSoftwareData = getSoftwareData;
win.getSoftwareFormData = getSoftwareFormData;
win.getSoftwareEditFormData = getSoftwareEditFormData;
win.getSimpleSoftwareFormData = getSimpleSoftwareFormData;
win.curateEditFormInit = curateEditFormInit;