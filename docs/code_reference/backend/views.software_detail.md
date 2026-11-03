[← Back to Backend](index.md)

# views/software_detail.py

The view for a published software's landing page. Touch this when changing
how a software detail page is looked up or what data its template receives.

**Source:** [django/website/views/software_detail.py](../../../django/website/views/software_detail.py)

## Contents

- [Classes](#classes)

---

## Classes

### `SoftwareDetailView`

Displays a published software's landing page with all its metadata, looked up by slug or UUID. **Extends:** `DetailView`

| Member | Kind | Description |
|---|---|---|
| `model` | class attribute | `Software`. |
| `template_name` | class attribute | `'website/software_detail.html'`. |
| `context_object_name` | class attribute | `'software'`. |
| `get(request, *args, **kwargs)` | method | GET handler: redirects a UUID URL of a published software to its slug URL with a 302, otherwise renders the page. |
| `get_queryset()` | method | Only published (visible) software. |
| `get_object(queryset)` | method | The software for the URL's `pk`, or for its `slug`; 404 if no published software has that slug. |
| `get_context_data(**kwargs)` | method | Adds the latest version, ordered functionality tags, and an escaped JSON-LD serialization (`software_jsonld`) to the template context. |
