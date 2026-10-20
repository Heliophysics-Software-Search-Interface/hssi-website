[← Back to Home](../index.md)

# Code Reference

Detailed, look-up-oriented reference for the codebase's internals, grouped
by subsystem — the data model, the submission/curation pipeline, the
frontend, the admin/curation tooling, and deployment configuration. See
[Architecture](../architecture.md) first for the big picture; come back
here when you need the specifics of a particular part.

## Contents

- [Sections](#sections)

---

## Sections

- [Data Model](data_model.md) — the model layer: `HssiModel`/`HssiBase`,
  `ControlledList`/`ControlledGraphList`, and the core software/people/
  organization/vocabulary models.
- [Submission Workflow](submission_workflow.md) — how a submission moves
  from intake through curation to publication.
- [Frontend Architecture](frontend_architecture.md) — the TypeScript
  frontend's module structure and how it talks to the backend.
- [Admin & Curation](admin_and_curation.md) — the custom Django admin site
  and curator tooling.
- [Deployment Reference](deployment_reference.md) — exhaustive reference
  for the Docker/nginx/gunicorn deployment configuration.
