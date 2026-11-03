[← Back to Code Reference](../overview.md)

# Backend

Per-module reference for the commonly edited modules of the Django app
(`django/website/`). Each page lists the module's public constants, types,
classes, and functions with a short description of each.

## Contents

- [Models](#models)
- [Forms](#forms)
- [Views](#views)
- [Admin](#admin)
- [Shared](#shared)

---

## Models

- [models/base.py](models.base.md) — the abstract base models every model inherits from.
- [models/people.py](models.people.md) — people, curators, and submitters.
- [models/serializers/software.py](models.serializers.software.md) — the REST and JSON-LD serializer for `Software`.
- [models/software.py](models.software.md) — the software entry and its versions, submission info, visibility flag, and edit links.
- [models/structurizer.py](models.structurizer.md) — turns models into the structures the frontend builds forms from.
- [models/vocab.py](models.vocab.md) — the controlled vocabulary models.

## Forms

- [forms/controls/model_object_selector.py](forms.controls.model_object_selector.md) — a Django widget for picking existing model objects.
- [forms/names.py](forms.names.md) — shared names and tooltip text for submission form fields.
- [forms/submission_data.py](forms.submission_data.md) — the structures that define the submission form.

## Views

- [views/api/software_api.py](views.api.software_api.md) — the REST API for published software.
- [views/edit_submission.py](views.edit_submission.md) — the edit-link flow for existing submissions.
- [views/exposed_models.py](views.exposed_models.md) — form structures and choice lists for the frontend.
- [views/model_rows.py](views.model_rows.md) — model rows as JSON, filtered by access level.
- [views/search.py](views.search.md) — the software search endpoint.
- [views/software_detail.py](views.software_detail.md) — a published software's landing page.
- [views/submit.py](views.submit.md) — the public submission form and its save endpoint.

## Admin

- [admin/actions.py](admin.actions.md) — custom admin views for database export/import, metadata, and vocabulary refreshes.
- [admin/csv_export.py](admin.csv_export.md) — CSV export and import of every model.
- [admin/fetch_vocab.py](admin.fetch_vocab.md) — fetching controlled vocabularies from external sources.
- [admin/model_admin.py](admin.model_admin.md) — the admin and import/export classes for every model.

## Shared

- [data_parser.py](data_parser.md) — turns submission form data into database objects.
- [util.py](util.md) — access levels, homepage filter URLs, and reference-rewriting helpers.
