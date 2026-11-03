[← Back to Backend](index.md)

# models/people.py

Models for people involved with software entries: authors and contacts
(`Person`), curators, and submitters. Touch this when changing how people are
stored, displayed, or searched for in forms.

**Source:** [django/website/models/people.py](../../../django/website/models/people.py)

## Contents

- [Classes](#classes)

---

## Classes

### `Person`

Metadata about a person, such as a software author. **Extends:** `HssiModel`

| Member | Kind | Description |
|---|---|---|
| `access` | class attribute | `PUBLIC`. |
| `given_name` | field | Given (first) name. |
| `family_name` | field | Family (last) name. |
| `identifier` | field | Identifier URL, typically an ORCID. |
| `affiliation` | field | Affiliated `Organization`s. |
| `softwares` | field | Reverse relation to `Software` entries. |
| `submission_info` | field | Reverse relation to `SubmissionInfo` entries. |
| `curator` | field | Reverse relation to the person's `Curator` row. |
| `fullName` | property | Given and family name joined by a space; setting it splits on the first word. |
| `get_default_person()` | static method | The placeholder "UNKNOWN" person, created if it doesn't exist. |
| `get_search_terms()` | method | Name words plus the identifier and its ORCID ID. |
| `get_top_field()` | class method | Returns the `given_name` field as the model's display field. |
| `get_second_top_field()` | class method | Returns the `family_name` field as the model's secondary display field. |
| `to_str_lastname_firstname()` | method | The name as `"Family, Given"`, or just the given name if there is no family name. |

### `Curator`

A user who is able to curate submissions. **Extends:** `HssiModel`

| Member | Kind | Description |
|---|---|---|
| `access` | class attribute | `CURATOR`. |
| `email` | field | Curator's email address. |
| `person` | field | The curator's `Person`; defaults to the placeholder "UNKNOWN" person. |
| `submission_infos` | field | Reverse relation to `SubmissionInfo` entries the curator is assigned to. |
| `submission_infos_led` | field | Reverse relation to `SubmissionInfo` entries the curator leads. |
| `get_top_field()` | class method | Returns the `email` field as the model's display field. |

### `Submitter`

A person who has submitted a software. **Extends:** `HssiModel`

| Member | Kind | Description |
|---|---|---|
| `access` | class attribute | `CURATOR`. |
| `email` | field | Submitter's email address, or a JSON-style list of addresses. |
| `person` | field | The submitter's `Person`; defaults to the placeholder "UNKNOWN" person. |
| `submission_infos` | field | Reverse relation to `SubmissionInfo` entries. |
| `fullName` | property | The linked person's full name. |
| `email_list()` | method | The `email` field parsed as a list of addresses, or a single-item list if it isn't a list. |
| `get_default_submitter()` | static method | The placeholder submitter with email "UNKNOWN"; a newly created one is not saved. |
| `get_top_field()` | class method | Returns the `email` field as the model's display field. |
