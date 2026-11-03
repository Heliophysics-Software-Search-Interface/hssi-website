[← Back to Backend](index.md)

# forms/submission_data.py

Defines the `ModelStructure`s that describe the software submission form:
the top-level form, its three page sections, and the nested sub-forms for
authors, organizations, versions, related items and so on. All structures are
registered on import. Touch this when adding, removing, reordering or
reconfiguring a field on the submission form.

**Source:** [django/website/forms/submission_data.py](../../../django/website/forms/submission_data.py)

## Contents

- [Constants](#constants)

---

## Constants

| Name | Description |
|---|---|
| `SUBMISSION_FORM_AUTHOR_AFFILIATION` | `Organization` sub-form for an author's affiliation: name and ROR identifier. |
| `SUBMISSION_FORM_CONTRIBUTOR_AFFILIATION` | `Organization` sub-form for a contributor's affiliation: name and ROR identifier. |
| `SUBMISSION_FORM_PUBLISHER` | `Organization` sub-form for the publisher: name and ROR identifier. |
| `SUBMISSION_FORM_FUNDER` | `Organization` sub-form for a funder: name and ROR identifier. |
| `SUBMISSION_FORM_SUBMITTER` | `Submitter` sub-form: name and email. |
| `SUBMISSION_FORM_AUTHOR` | `Person` sub-form for an author: name, identifier, and nested affiliations. |
| `SUBMISSION_FORM_CONTRIBUTOR` | `Person` sub-form for a contributor: name, ORCID, and nested affiliations. |
| `SUBMISSION_FORM_VERSION` | `SoftwareVersion` sub-form: number, date, description and DOI. |
| `SUBMISSION_FORM_PUBLICATION` | `RelatedItem` sub-form for a publication DOI. |
| `SUBMISSION_FORM_REL_SOFTWARE` | `RelatedItem` sub-form for a related or interoperable software DOI. |
| `SUBMISSION_FORM_INSTRUMENT` | `InstrumentObservatory` sub-form for a related instrument: name and identifier URL. |
| `SUBMISSION_FORM_OBSERVATORY` | `InstrumentObservatory` sub-form for a related observatory: name and identifier URL. |
| `SUBMISSION_FORM_DATASET` | `RelatedItem` sub-form for a related dataset DOI. |
| `SUBMISSION_FORM_LICENSE` | `License` sub-form: name and URL. |
| `SUBMISSION_FORM_AWARD` | `Award` sub-form: title and number. |
| `SUBMISSION_FORM_FIELDS` | The full `Software` submission form, in display order, using the sub-forms above for nested fields. |
| `SUBMISSION_FORM_FIELDS_1` | First page section of `SUBMISSION_FORM_FIELDS`: the fields before `keywords`. |
| `SUBMISSION_FORM_FIELDS_2` | Second page section: from `keywords` up to `related_publications`. |
| `SUBMISSION_FORM_FIELDS_3` | Third page section: from `related_publications` to the end. |
