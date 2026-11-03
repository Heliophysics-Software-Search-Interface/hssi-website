[← Back to Backend](index.md)

# views/search.py

The search endpoint for published software: parses `field:"value"` filters,
then ranks plain-text matches in tiers by which fields they hit. Touch this
when adding a search field alias or changing search ranking.

**Source:** [django/website/views/search.py](../../../django/website/views/search.py)

## Contents

- [Functions](#functions)

---

## Functions

| Function | Description |
|---|---|
| `parse_field_queries(raw_query)` | Extracts `field:"value"` tokens from a query; returns the `(alias, value)` pairs and the query with those tokens removed. |
| `build_author_query(value)` | Builds a `Q` matching authors whose given or family name contains any word of the value; for multi-word values also matches a single person by first and last word. |
| `build_field_query(query, tokens, fields)` | Builds a case-insensitive OR `Q` matching the full query or any token in any of the fields. |
| `serialize_results(result_ids, mode, request)` | Returns JSON results as plain IDs (`mode` `"id"`) or as JSON-LD serializations in the given order. |
| `search_visible_software(request)` | GET: searches published software by the `q` parameter, applying field filters as AND conditions and ranking the remaining text in tiers; returns results per the `mode` parameter (`id` or `jsonld`, default `jsonld`). |
