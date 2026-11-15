[← Back to Code Reference](overview.md)

# Submission Workflow

The code path behind the submission lifecycle: which views, functions, and 
models handle each step from intake through curation, publishing, and later 
edits. See [Architecture](../architecture.md#submission-lifecycle) for the 
same process from the submitter's and curator's point of view.

## Contents

- [Intake](#intake)
- [Records Created](#records-created)
- [Notifications](#notifications)
- [Curation and Publishing](#curation-and-publishing)
- [Edits](#edits)
- [Two Parsers](#two-parsers)

---

## Intake

There are three ways a submission enters the system. Each one saves its 
submissions inside a single database transaction, so a failure part way 
through saves nothing.

| Path | Handled by | Parsed by |
|---|---|---|
| Submission form (`/submit/` → `POST /submit/submit_data/`) | [`views/submit.py`](../../django/website/views/submit.py) `submit_data` | [`data_parser.py`](../../django/website/data_parser.py) `handle_submission_data` |
| `POST /api/submission/` | [`views/api/software_api.py`](../../django/website/views/api/software_api.py) `SubmissionAPI` | [`SubmissionSerializer`](../../django/website/models/serializers/submission.py) |
| `POST /api/submit` (legacy) | [`views/api_submit.py`](../../django/website/views/api_submit.py) `api_submit` | `api_submission_to_formdict`, then `handle_submission_data` |

The form path redirects to `/submit/submitted/` on success. Both API paths 
return the new software IDs. The request and response formats for the APIs 
are in the [Submission API reference](../api_reference/submission_api.md).

## Records Created

Each submission creates:

- A [`Software`](../../django/website/models/software.py) entry holding the 
submitted metadata, along with any related objects it references (people, 
organizations, keywords, versions, and so on)
- A `SubmissionInfo` entry recording the submission date and its submitters
- A `SoftwareEditQueue` entry, whose ID is the submitter's edit link, set to 
expire after 90 days

The new `Software` is not yet visible on the site, because it has no 
`VerifiedSoftware` entry (see [Curation and Publishing](#curation-and-publishing)).

## Notifications

Once the transaction commits, each submission:

- Emails the edit link to every submitter email address 
(`email_existing_edit_link` in 
[`views/edit_submission.py`](../../django/website/views/edit_submission.py))
- Opens a "New submission" GitHub issue with the `new submission` label, so 
curators know to review it (`open_submission_issue` in `views/submit.py`). 
This is skipped if `HSSI_GITHUB_TOKEN` isn't set.

The email needs `GMAIL_EMAIL` and `GMAIL_APP_PASSWORD` to be set (see the 
[Deployment Reference](deployment_reference.md#environment-variables)).

## Curation and Publishing

Curators review new entries in the Django admin at `/admin/`. When an entry 
is ready, they select it in the `Software` list and run the **Publish to 
Visible Software** action (`mark_visible` in 
[`admin/model_admin.py`](../../django/website/admin/model_admin.py)).

This calls `VerifiedSoftware.create_verified`, which creates a 
`VerifiedSoftware` row sharing the software's UUID and gives it a unique URL 
slug built from the software's name. From then on the entry appears in 
search, in the public API, and at its own landing page. Entries that are 
already published are skipped.

The same admin list also has an **Add to Edit Queue** action, which creates a 
new 31-day edit link for the selected entries.

## Edits

A submitter edits an entry through an edit link, which opens 
`/curate/edit_submission/?uid=<edit link ID>`. All edit views are in 
[`views/edit_submission.py`](../../django/website/views/edit_submission.py):

1. If the original link has expired, the submitter asks for a new one from 
the software's landing page. The page shows a masked version of the 
submitter emails (`GET /api/masked_emails/<id>/`), and the submitter types 
the full address in.
2. `request_edit_link` checks that the address matches one of the entry's 
submitters, then emails a new 90-day edit link.
3. The edit page loads the entry's current data from 
`/sapi/software_edit_data/<edit link ID>/` into the form.
4. Saving posts to `/curate/edit_submission/submit_data/<edit link ID>/`, 
where `submit_edits` checks the link hasn't expired and passes the data to 
`handle_submission_data` with the existing `Software` as its target.

Edits are applied immediately, including to entries that are already 
published, with no curator review.

Separately, `PATCH /api/data/software/<id>/` updates a published entry 
directly through `SubmissionSerializer`, protected by `HSSI_UPDATE_TOKEN` 
instead of an edit link.

## Two Parsers

Submission data is parsed by two separate implementations:

- [`data_parser.py`](../../django/website/data_parser.py) 
`handle_submission_data`, used by the submission form, form edits, and the 
legacy `/api/submit`
- [`SubmissionSerializer`](../../django/website/models/serializers/submission.py), 
used by `POST /api/submission/` and the `PATCH` update API

They expect different field names and validate differently. When adding or 
changing a submission field, update both, along with the form field 
definitions in [`forms/names.py`](../../django/website/forms/names.py) and 
[`forms/submission_data.py`](../../django/website/forms/submission_data.py).
