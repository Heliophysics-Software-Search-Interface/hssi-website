import { 
	base64ToUuid,
	FilterGroup,
	FilterGroupMode,
	isUuid4,
	ModelDataCache,
	uuidToBase64,
	type ModelName,
	type SoftwareDataAsync,
} from "../loader";

const urlUidTruncateLength = 6;
const urlSymOr = "_";
const urlSymAnd = "-";
const urlSymNot = "~";
const urlSymUidDelim = ".";
const uidUrlEncodeLength = 7;

const softwareFieldParamPairs: [keyof SoftwareDataAsync, string][] = [
	["programmingLanguage", "p"],
	["publisher", "pub"],
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
	const model = softwareFieldToModelMap[field];
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

export function filterGroupToUrlVal(group: FilterGroup): string{
	let valStr = "";

	for(const item of group.includedItems) {
		const uidTruncated = shortenUidToParamVal(item.id, item.targetSoftwareField);
		valStr += uidTruncated;
		if(group.mode == FilterGroupMode.And) valStr += urlSymAnd;
		else valStr += urlSymOr;
	}

	for(const item of group.excludedItems) {
		const uidTrunc = shortenUidToParamVal(item.id, item.targetSoftwareField);
		valStr += urlSymNot + uidTrunc;
		if(group.mode == FilterGroupMode.And) valStr += urlSymAnd;
		else valStr += urlSymOr;
	}

	// clip off final and/or symbol
	if (valStr.length > 0) valStr = valStr.substring(0, valStr.length - 1);

	return valStr;
}
