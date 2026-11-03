[← Back to Backend](index.md)

# admin/model_admin.py

Django admin classes for every HSSI model: a shared base admin with cleanup
actions, plus an import/export `Resource` and an admin class per model. Touch
this when adding a model to the admin site or adding an admin action.

**Source:** [django/website/admin/model_admin.py](../../../django/website/admin/model_admin.py)

## Contents

- [Classes](#classes)

---

## Classes

### `HSSIModelAdmin`

Base admin for HSSI models, with CSV import/export and actions for repairing and merging entries. **Extends:** `ImportExportModelAdmin`

| Member | Kind | Description |
|---|---|---|
| `actions` | class attribute | `[fix_uuid_chains, collapse_model_entries]`. |
| `list_display` | class attribute | `('str_display', 'id')`. |
| `fix_uuid_chains(request, queryset)` | method | Admin action "Fix Improper Toplevel UUID": for entries whose name is actually a UUID of another entry, follows the chain to the real entry and repoints all references to it. |
| `collapse_model_entries(request, queryset)` | method | Admin action "Collapse to Single": merges the selected entries into one via `HssiModel.collapse_objects` and repoints all references to it. |
| `str_display(obj)` | method | List column showing `str(obj)`. |

### `KeywordAdmin`

Admin for `Keyword`, with keyword-specific merge and name formatting actions. **Extends:** `HSSIModelAdmin`

| Member | Kind | Description |
|---|---|---|
| `resource_class` | class attribute | `KeywordResource`. |
| `actions` | class attribute | `fix_uuid_chains`, `collapse_keyword_entries`, `format_names`. |
| `collapse_keyword_entries(request, queryset)` | method | Admin action "Collapse to Single": merges the selected keywords and normalizes the result's name. |
| `format_names(req, query)` | method | Admin action "Format Names": replaces `_`, `-` and `.` with spaces and lowercases each selected keyword's name. |

### `RegionAdmin`

Admin for `Region` that also lists each region's full name. **Extends:** `HSSIModelAdmin`

| Member | Kind | Description |
|---|---|---|
| `resource_class` | class attribute | `RegionResource`. |
| `list_display` | class attribute | `("name", "full_name", "id")`. |
| `full_name(obj)` | method | List column showing the region's full name. |

### `InstrumentObservatoryAdmin`

Admin for `InstrumentObservatory` that shows each entry's identifier. **Extends:** `HSSIModelAdmin`

| Member | Kind | Description |
|---|---|---|
| `resource_class` | class attribute | `InstrumentObservatoryResource`. |
| `str_display(obj)` | method | `str(obj)`, plus the identifier in parentheses if set. |

### `LicenseAdmin`

Admin for `License` that shows the URL of "Other" licenses. **Extends:** `HSSIModelAdmin`

| Member | Kind | Description |
|---|---|---|
| `resource_class` | class attribute | `LicenseResource`. |
| `str_display(obj)` | method | `str(obj)`, plus the URL for a license named "Other". |

### `OrganizationAdmin`

Admin for `Organization` that shows each organization's ROR ID. **Extends:** `HSSIModelAdmin`

| Member | Kind | Description |
|---|---|---|
| `resource_class` | class attribute | `OrganizationResource`. |
| `str_display(obj)` | method | `str(obj)`, plus the identifier with any `ror.org` prefix removed. |

### `SoftwareAdmin`

Admin for `Software`, with actions to publish entries and create edit links. **Extends:** `HSSIModelAdmin`

| Member | Kind | Description |
|---|---|---|
| `resource_class` | class attribute | `SoftwareResource`. |
| `actions` | class attribute | `mark_visible`, `add_edit_queue`, `fix_uuid_chains`, `collapse_model_entries`. |
| `mark_visible(request, queryset)` | method | Admin action "Publish to Visible Software": publishes each selected software that isn't already published. |
| `add_edit_queue(request, queryset)` | method | Admin action "Add to Edit Queue": creates a 31-day edit link for each selected software. |
| `save_related(request, form, formsets, change)` | method | Saves related objects, then stamps `date_modified` if any field changed. |

### `VerifiedSoftwareAdmin`

Admin for `VerifiedSoftware` that also lists each entry's slug. **Extends:** `HSSIModelAdmin`

| Member | Kind | Description |
|---|---|---|
| `resource_class` | class attribute | `VerifiedSoftwareResource`. |
| `list_display` | class attribute | `("str_display", "slug")`. |

### `SoftwareEditQueueAdmin`

Admin for `SoftwareEditQueue` edit links. **Extends:** `ImportExportModelAdmin`

| Member | Kind | Description |
|---|---|---|
| `resource_class` | class attribute | `SoftwareEditQueueResource`. |
| `list_display` | class attribute | `('target_name', 'created', 'id')`. |
| `actions` | class attribute | `[remove_selected]`. |
| `remove_selected(request, query)` | method | Admin action "Prune expired items": deletes the selected links older than `default_expire_delta`. |
| `target_name(obj)` | method | List column showing the linked software's name, or `"None"`. |

### `SubmissionInfoAdmin`

Admin for `SubmissionInfo`, newest first, with an action to email edit links. **Extends:** `HSSIModelAdmin`

| Member | Kind | Description |
|---|---|---|
| `resource_class` | class attribute | `SubmissionInfoResource`. |
| `ordering` | class attribute | `("-submission_date",)`. |
| `actions` | class attribute | `email_edit_link`, `fix_uuid_chains`, `collapse_model_entries`. |
| `list_display` | class attribute | `('submission_name', 'submitter_name', 'submission_date', 'id')`. |
| `email_edit_link(request, query)` | method | Admin action "Email edit submission link (90 days)": creates and emails a 90-day edit link for each selected submission. |
| `submission_name(obj)` | method | List column showing the software's name, or `"<None>"`. |
| `submitter_name(obj)` | method | List column showing the first submitter's full name, or `"<None>"`. |

### Per-model Resource/Admin classes

Each `Resource` is an import/export `ModelResource` for one model; each admin is an `HSSIModelAdmin` that only sets `resource_class` to its paired resource.

| Class | Kind | Description |
|---|---|---|
| `OperatingSystemResource` / `OperatingSystemAdmin` | resource / admin | `OperatingSystem`. |
| `CpuArcitectureResource` / `CpuArchitectureAdmin` | resource / admin | `CpuArchitecture`. |
| `PhenomenaTypeResource` / `PhenomenaTypeAdmin` | resource / admin | `Phenomena`. |
| `DataInputResource` / `DataInputAdmin` | resource / admin | `DataInput`. |
| `RepoStatusResource` / `RepoStatusAdmin` | resource / admin | `RepoStatus`. |
| `FunctionCategoryResource` / `FunctionCategoryAdmin` | resource / admin | `FunctionCategory`. |
| `FileFormatResource` / `FileFormatAdmin` | resource / admin | `FileFormat`. |
| `ProgrammingLanguageResource` / `ProgrammingLanguageAdmin` | resource / admin | `ProgrammingLanguage`. |
| `PersonResource` / `PersonAdmin` | resource / admin | `Person`. |
| `CuratorResource` / `CuratorAdmin` | resource / admin | `Curator`. |
| `SubmitterResource` / `SubmitterAdmin` | resource / admin | Submitters; note the resource's `Meta.model` is `Person`, not `Submitter`. |
| `AwardResource` / `AwardAdmin` | resource / admin | `Award`. |
| `DatasetResource` / `DatasetAdmin` | resource / admin | `RelatedItem`. |
| `SoftwareVersionResource` / `SoftwareVersionAdmin` | resource / admin | `SoftwareVersion`. |
| `KeywordResource` | resource | `Keyword`; used by `KeywordAdmin`. |
| `RegionResource` | resource | `Region`; used by `RegionAdmin`. |
| `InstrumentObservatoryResource` | resource | `InstrumentObservatory`; used by `InstrumentObservatoryAdmin`. |
| `LicenseResource` | resource | `License`; used by `LicenseAdmin`. |
| `OrganizationResource` | resource | `Organization`; used by `OrganizationAdmin`. |
| `SoftwareResource` | resource | `Software`; used by `SoftwareAdmin`. |
| `VerifiedSoftwareResource` | resource | `VerifiedSoftware`; used by `VerifiedSoftwareAdmin`. |
| `SoftwareEditQueueResource` | resource | For `SoftwareEditQueue`, used by `SoftwareEditQueueAdmin`; its `Meta` sets `Model` (capitalized), so `Meta.model` is not actually set. |
| `SubmissionInfoResource` | resource | `SubmissionInfo`; used by `SubmissionInfoAdmin`. |
