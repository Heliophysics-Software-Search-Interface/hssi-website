[← Back to Backend](index.md)

# views/exposed_models.py

Views that expose the form structures and model choices the frontend form
system needs, plus the generic single-model form page. Touch this when the
frontend needs new form structure data or choice lists.

**Source:** [django/website/views/exposed_models.py](../../../django/website/views/exposed_models.py)

## Contents

- [Functions](#functions)

---

## Functions

| Function | Description |
|---|---|
| `get_model_structure(request)` | Returns JSON of every registered form structure, serialized, plus the model field map. |
| `get_model_choices(request, model_name)` | Returns JSON of the choices for every object of an `HssiModel`, filtered by the GET parameters (evaluated as Python literals); 400 if the model is not an `HssiModel`. |
| `model_form(request, model_name)` | Renders the model form page for the named form structure. |
