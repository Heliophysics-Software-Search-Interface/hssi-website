[← Back to Backend](index.md)

# views/edit_submission.py

Views and helpers for editing an existing submission through an emailed edit
link: requesting a link, loading the submission's data, and saving edits.
Touch this when changing the edit-link flow or the emails it sends.

**Source:** [django/website/views/edit_submission.py](../../../django/website/views/edit_submission.py)

## Contents

- [Functions](#functions)

---

## Functions

| Function | Description |
|---|---|
| `get_masked_submitter_emails(request, uid)` | GET only: returns JSON with the masked submitter emails of a software, so the user can tell which email to enter. |
| `request_edit_link(request, uid)` | POST only: if the request body matches a submitter email of the software, emails a new edit link and returns 204; otherwise 400. |
| `get_submission_data(request, uid)` | Returns JSON of the software and first submitter for an edit link UID; 400 if the link is invalid or expired. |
| `edit_submission(request)` | Renders the edit submission page with the names of the three submission form structures. |
| `submit_edits(request, uid)` | Saves the JSON request body as edits to the edit link's software in one transaction and returns 204; 400 if the link is invalid or expired, 500 on failure. |
| `email_existing_edit_link(submission)` | Emails the submitters the software's edit link that expires last; returns `False` if no unexpired link exists. |
| `email_edit_link(submission, expire_time)` | Creates a new edit link for the submission's software, expiring after 90 days by default, and emails it to the submitters. |
