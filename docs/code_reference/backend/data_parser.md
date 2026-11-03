[← Back to Backend](index.md)

# data_parser.py

Turns submission form data into database objects: resolves or creates the
referenced people, organizations and vocabulary terms, and writes them onto a
`Software` entry. Touch this when changing how a submitted field is stored,
or how the REST API submission schema maps onto the form data.

**Source:** [django/website/data_parser.py](../../../django/website/data_parser.py)

## Contents

- [Functions](#functions)

---

## Functions

| Function | Description |
|---|---|
| `api_submission_to_formdict(item)` | Converts a REST API submission object into the form-data dict expected by `handle_submission_data`; raises `ValueError` if required fields are missing or malformed. |
| `parse_organization(data, name_field, ident_field, allow_creation)` | Resolves an `Organization` from form data by UUID, identifier, then name, creating one (with an abbreviation taken from any parentheses in the name) if allowed; returns `None` if there is no name or no match. |
| `parse_person(data, name_field, ident_field, affil_field, affil_ident_field)` | Resolves a `Person` from form data by UUID or identifier, otherwise creates one from the name, then adds any affiliations. |
| `parse_controlled_list(target_model, name, identifier, definition, allow_creation, name_match_fallback)` | Resolves a controlled-list term by UUID, identifier, then name, creating one if allowed; raises if nothing matches. |
| `apply_software_core_fields(software, data)` | Sets the software's scalar fields (persistent identifier, repository URL, name, descriptions, documentation) from submission data. |
| `apply_reference_publication(software, data)` | Resolves or creates the reference publication `RelatedItem` by identifier and assigns it. |
| `apply_development_status(software, data)` | Resolves and assigns the software's `RepoStatus`. |
| `apply_logo(software, data)` | Sets the software's logo URL. |
| `split_firstname_lastname(submitter_name)` | Splits a full name into `(first, last)`, taking the last word as the last name. |
| `resolve_submitter(data)` | Returns the existing `Submitter` with the same email and person, or creates a new submitter and person. |
| `build_submission_info(data)` | Creates and saves a `SubmissionInfo` with initial-submission defaults and the resolved submitter. |
| `apply_license(software, data)` | Resolves the software's `License` by UUID, name, then URL; creates an "Other" license for an unknown URL, or uses the default other license if there is no URL. |
| `apply_publisher(software, data)` | Resolves and assigns the publisher `Organization`, using the existing Zenodo organization if the name is "zenodo". |
| `apply_version(software, data)` | Creates a `SoftwareVersion` from the version data and adds it to the software. |
| `apply_authors(software, data)` | Replaces the software's authors with `Person`s resolved from the author data. |
| `apply_publication_date(software, data)` | Parses a `YYYY-MM-DD` publication date and sets it on the software. |
| `apply_controlled_m2m(software, data, field_key, target_model, m2m_attr, allow_creation)` | Replaces a controlled-list many-to-many field on the software with terms resolved from the data. |
| `apply_function_category(software, fullnames)` | Sets the software's functionality categories from `"Parent: Child"` full names or UUIDs, deduplicated in order; raises if a category doesn't exist. |
| `apply_keywords(software, data)` | Replaces the software's keywords, creating a normalized lowercase `Keyword` when no existing one matches. |
| `apply_awards(software, data)` | Replaces the software's awards with `Award`s resolved by UUID or award number, creating new ones as needed. |
| `apply_funders(software, data)` | Replaces the software's funders with resolved `Organization`s. |
| `apply_related_items(software, items, m2m_attr, item_type)` | Replaces a `RelatedItem` many-to-many field with items resolved or created from identifiers; new items get the given type and the name "UNKNOWN". |
| `apply_related_instruments(software, data)` | Replaces the software's related instruments, resolved by UUID or identifier or created as new instruments. |
| `apply_related_observatories(software, data)` | Replaces the software's related observatories, resolved by UUID or identifier or created as new observatories. |
| `handle_submission_data(data, software_target)` | Stores submission data in the given software (or a new one), creates its `SubmissionInfo`, applies every field, and returns the `SubmissionInfo`'s ID. |
