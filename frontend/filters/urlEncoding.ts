import { 
	FilterGroup,
	FilterGroupMode,
	FilterMenu,
	FilterMenuItem,
	isUuid4,
	ModelDataCache,
	type ModelName,
	type SoftwareDataAsync,
} from "../loader";

const urlSymAnd = "~";
const urlSymNot = "~";
const urlSymUidDelim = ".";
const uidUrlEncodeLength = 7;

const softwareFieldParamPairs: [keyof SoftwareDataAsync, string][] = [
	["programmingLanguage", "p"],
	["publisher", "pb"],
	["authors", "a"],
	["relatedInstruments", "i"],
	["relatedObservatories", "o"],
	["version", "v"],
	["referencePublication", "pn"],
	["softwareFunctionality", "f"],
	["dataSources", "ds"],
	["inputFormats", "if"],
	["outputFormats", "of"],
	["cpuArchitecture", "cpu"],
	["relatedPublications", "rp"],
	["relatedDatasets", "rd"],
	["developmentStatus", "s"],
	["operatingSystem", "os"],
	["license", "l"],
	["relatedRegion", "r"],
	["keywords", "k"],
	["relatedSoftware", "rs"],
	["interoperableSoftware", "is"],
	["funder", "fn"],
	["award", "aw"],
	["relatedPhenomena", "ph"],
];

const softwareFieldToModelMap: {[key: keyof SoftwareDataAsync]: ModelName} = {
	programmingLanguage: "ProgrammingLanguage",
	publisher: "Organization",
	authors: "Person",
	relatedInstruments: "InstrumentObservatory",
	relatedObservatories: "InstrumentObservatory",
	version: "SoftwareVersion",
	referencePublication: "RelatedItem",
	softwareFunctionality: "FunctionCategory",
	dataSources: "DataInput",
	inputFormats: "FileFormat",
	outputFormats: "FileFormat",
	cpuArchitecture: "CpuArchitecture",
	relatedPublications: "RelatedItem",
	relatedDatasets: "RelatedItem",
	developmentStatus: "RepoStatus",
	operatingSystem: "OperatingSystem",
	license: "License",
	relatedRegion: "Region",
	keywords: "Keyword",
	relatedSoftware: "Software",
	interoperableSoftware: "Software",
	funder: "Organization",
	award: "Award",
	relatedPhenomena: "Phenomena",
}

const softwareFieldToUrlParamMap: Map<keyof SoftwareDataAsync, string> = new Map();
const urlParamToSoftwareFieldMap: Map<string, keyof SoftwareDataAsync> = new Map();

function initMaps(): void {
	for(const pair of softwareFieldParamPairs){
		softwareFieldToUrlParamMap.set(pair[0], pair[1]);
		urlParamToSoftwareFieldMap.set(pair[1], pair[0]);
	}
}
initMaps();

function urlParamToSoftwareField(urlParamName: string): keyof SoftwareDataAsync {
	return urlParamToSoftwareFieldMap.get(urlParamName);
}

function softwareFieldToUrlParam(fieldName: keyof SoftwareDataAsync): string {
	return softwareFieldToUrlParamMap.get(fieldName);
}

/**
 * truncates the uid based on settings in the urlEncoding module, and returns 
 * the base 64 encoded result to shorten it even further
 * @param uid the full uid to shorten
 * @param field the field that the uid is meant to be a filter value for
 */
function shortenUidToParamVal(uid: string, field: keyof SoftwareDataAsync): string{
	if(!isUuid4(uid)) throw new Error("Invalid UUID format: " + uid.toString());
	const truncated = uuidToBase64(uid).substring(0, uidUrlEncodeLength);
	return truncated + softwareFieldToUrlParam(field);
}

/**
 * since the uids in url parameter values are shortened to save space, they 
 * must be expanded again before they are used in queries, this will expand the
 * given url parameter value to a full uid
 * @param val the parameter value to expand into a uid
 * @returns 
 */
async function expandUidFromParamVal(val: string): Promise<string> {
	const truncatedUid = base64ToUuid(val.substring(0, uidUrlEncodeLength));
	const field = urlParamToSoftwareField(val.substring(uidUrlEncodeLength));
	const model = softwareFieldToModelName(field);
	return await getUidFromTruncated(truncatedUid, model);
}

/**
 * since the uids in url parameters are shortened to save space, they must be 
 * expanded again before they are used in queries, this will match truncated
 * shortened uids against known uids for the specified model and retun the 
 * full uid of the first match
 * @param truncatedUid the first n characters of the full uid that you're 
 * 	looking for (where n is any number less than the full length of the uid)
 * @param model the model to search for the uid in
 */
async function getUidFromTruncated(truncatedUid: string, model: ModelName): Promise<string>{
	if(isUuid4(truncatedUid)) return truncatedUid;
	const cache = ModelDataCache.getCache(model);
	if(cache.hasFetchedAllData) return cache.expandUidFromTruncated(truncatedUid);
	await cache.fetchAllData();
	return cache.expandUidFromTruncated(truncatedUid);
}

function multiItemToUrlVal(item: FilterMenuItem, negated: boolean): string{
	let valStr = "";

	for(const sub of item.subItems){
		if(negated) valStr += urlSymNot;
		valStr += shortenUidToParamVal(sub.id, sub.targetSoftwareField) + urlSymUidDelim;
	}
	if (valStr.length > 0) valStr = valStr.substring(0, valStr.length - 1);

	return valStr;
}

export function softwareFieldToModelName(field: keyof SoftwareDataAsync): ModelName {
	return softwareFieldToModelMap[field];
}

export function filterGroupToUrlVal(group: FilterGroup): string{
	let valStr = "";

	for(const item of group.includedItems) {
		let truncated: string = null;
		if(!item.id && item.subItems?.length > 0) truncated = multiItemToUrlVal(item, false);
		else truncated = shortenUidToParamVal(item.id, item.targetSoftwareField);
		valStr += truncated + urlSymUidDelim;
	}

	for(const item of group.excludedItems) {
		let trunc: string = null;
		if(!item.id && item.subItems?.length > 0) trunc = multiItemToUrlVal(item, true);
		else trunc = urlSymNot + shortenUidToParamVal(item.id, item.targetSoftwareField);
		valStr += trunc + urlSymUidDelim;
	}

	// clip off final and/or symbol
	if (valStr.length > 0) valStr = valStr.substring(0, valStr.length - 1);

	if(group.mode == FilterGroupMode.And) valStr += urlSymAnd;
	return valStr;
}

export async function urlValToFilterGroup(urlVal: string): Promise<FilterGroup>{
	const group = new FilterGroup();
	let newval = urlVal.trim();

	// parse mode
	if(newval.endsWith(urlSymAnd)) {
		group.mode = FilterGroupMode.And;
		newval = newval.substring(0, newval.length - 1);
	}
	else group.mode = FilterGroupMode.Or;

	// split into individual values
	const vals = newval.split(urlSymUidDelim);
	for (let val of vals) {

		// check to see if the filter item is negated
		let itemList = null 
		if(!val.startsWith(urlSymNot)) itemList = group.includedItems 
		else {
			itemList = group.excludedItems;
			val = val.substring(1);
		}

		// convert to uid and find corresponding filtermenuitem
		const uid = await expandUidFromParamVal(val);
		const field = urlParamToSoftwareField(val.substring(uidUrlEncodeLength));
		const tab = FilterMenu.main.getTabForField(field);
		const item = await tab.findItemWithUid(uid);

		itemList.push(item);
	}

	return group;
}

/** Convert UUID (full or partial) → Base64 (URL-safe optional) */
export function uuidToBase64(uuid: string): string {
	const hex = uuid.replace(/-/g, "").toLowerCase();
	const bytes = new Uint8Array(hex.length / 2);

	for (let i = 0; i < bytes.length; i++) {
		bytes[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
	}

	const b64 = btoa(String.fromCharCode(...bytes)).replace(/=+$/, "");
	return b64.replaceAll("+", "-").replaceAll("/", "_");
}

/** Convert Base64 back → UUID hex string */
export function base64ToUuid(b64: string): string {
	// Undo URL-safe variant if used
	const normalized = b64.replaceAll("-", "+").replaceAll("_", "/");

	const bin = atob(normalized);
	let hex = "";
	for (let i = 0; i < bin.length; i++) {
		hex += bin.charCodeAt(i).toString(16).padStart(2, "0");
	}

	// Add dashes
	const parts = [8, 12, 16, 20, 32];
	let out = "";
	let lastpart = 0;

	for (const part of parts) {
		// no more chars
		if (hex.length <= lastpart) break; 

		const end = Math.min(part, hex.length);
		out += hex.slice(lastpart, end);
		
		// add dash only if a full block exists
		if (end === part && end < hex.length) out += "-";  
		lastpart = part;
	}

	return out;
}

const win = window as any;
win.expandUidFromParamVal = expandUidFromParamVal;
win.shortenUidToParamVal = shortenUidToParamVal;
win.getUidFromTruncated = getUidFromTruncated;