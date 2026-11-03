[← Back to Backend](index.md)

# forms/names.py

String constants shared by the submission form definitions: form property
keys, widget type names, form field names, model row names, and the tooltip
text shown for each field. Touch this when adding or renaming a submission
form field or editing its help text.

**Source:** [django/website/forms/names.py](../../../django/website/forms/names.py)

## Contents

- [Constants](#constants)

---

## Constants

| Name | Description |
|---|---|
| `PROP_LABEL` | `"label"`: form field property key for the field's label. |
| `PROP_TT_EXPL` | `"tooltipExplanation"`: form field property key for the explanation tooltip. |
| `PROP_TT_BEST` | `"tooltipBestPractise"`: form field property key for the best-practice tooltip. |
| `PROP_WIDGET_PROPS` | `"widgetProperties"`: form field property key for the widget's own properties. |
| `PROP_TOPFIELD` | `"topField"`: form field property key marking the top field. |
| `WPROP_*` | Widget property keys passed to frontend widgets: `maxLength`, `targetModel`, `modelFilter`, `dropdownButton`, `allowNewEntries`, `resultFilters`, `licenseModelbox`. |
| `TYPE_*` | Frontend widget class names, e.g. `TYPE_CHAR` (`"CharWidget"`), `TYPE_ORCID` (`"OrcidWidget"`), `TYPE_MODELBOX` (`"ModelBox"`). |
| `FIELD_*` | Submission form field names, one per field, e.g. `FIELD_SOFTWARENAME` (`"software_name"`), `FIELD_AUTHORIDENTIFIER` (`"authorIdentifier"`). |
| `ROW_*` | Model attribute names that form fields map to, named `ROW_<MODEL>_<ATTRIBUTE>`, e.g. `ROW_PERSON_NAME` (`"fullName"`). |
| `TTEXPL_*` | Explanation tooltip text for each form field, named after its `FIELD_*` constant. |
| `TTBEST_*` | Best-practice tooltip text for each form field, named after its `FIELD_*` constant. |
| `MODEL_FIELD_MAP` | Maps each `FIELD_*` name to the model attribute it is stored in, or `"NONE"` if it isn't stored; sent to the frontend by the exposed models view. |
