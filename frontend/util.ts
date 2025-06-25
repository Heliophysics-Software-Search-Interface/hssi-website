
export type JSONValue = string | number | boolean | null | JSONObject | JSONArray;
export interface JSONObject { [key: string]: JSONValue }
export interface JSONArray<T = JSONValue> extends Array<T> {}

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
) {
    const controller = new AbortController();
    const reqInit = deepMerge(
        init as JSONObject, 
        {signal: controller.signal}, 
        true
    );
    const timeoutId = setTimeout(() => controller.abort(), timeout * 1000);
    const result = await fetch(input, reqInit);
    clearTimeout(timeoutId);
    return result;
}