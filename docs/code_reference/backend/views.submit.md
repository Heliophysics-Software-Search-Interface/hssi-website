[← Back to Backend](index.md)

# views/submit.py

Views for the public software submission form: the form page, the
confirmation page, and the endpoint that saves a new submission. Touch this
when changing what happens when someone submits a new software entry.

**Source:** [django/website/views/submit.py](../../../django/website/views/submit.py)

## Contents

- [Functions](#functions)

---

## Functions

| Function | Description |
|---|---|
| `view_form(request)` | Renders the submission form page with the names of the three submission form structures. |
| `view_confirmation(request)` | GET only: renders the submission confirmation page; 400 for other methods. |
| `submit_data(request)` | POST only: saves the JSON form data as a new submission in one transaction, creates a 90-day edit link, and on commit opens a "new submission" GitHub issue and emails the edit link to the submitters, then redirects to the confirmation page. |
| `open_submission_issue(software, through)` | Opens a "new submission" GitHub issue naming the software and whether it came through the form or the API; does nothing if `HSSI_GITHUB_TOKEN` is unset. |
