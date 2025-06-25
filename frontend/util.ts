
export type JSONValue = string | number | boolean | null | JSONObject | JSONArray;
export interface JSONObject { [key: string]: JSONValue }
export interface JSONArray<T = JSONValue> extends Array<T> {}

