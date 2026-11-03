[← Back to Code Reference](../overview.md)

# Frontend

Per-module reference for the commonly edited modules of the TypeScript
frontend (`frontend/`). Each page lists the module's exported constants and
types, and the public and protected members of its classes, with a short
description of each.

## Contents

- [Entry Points](#entry-points)
- [Forms](#forms)
- [Filters](#filters)
- [Model Data](#model-data)
- [Resources](#resources)
- [Dialogues](#dialogues)

---

## Entry Points

- [index.ts and loader.ts](loader.md) — the entry point and the barrel module every import goes through.
- [util.ts](util.md) — shared helpers, JSON types, and API URLs.

## Forms

- [forms/formGenerator.ts](forms.formGenerator.md) — builds, validates, and submits the submission/edit form.
- [forms/fieldRequirement.ts](forms.fieldRequirement.md) — requirement levels and invalid-field highlighting.
- [forms/fields/modelFieldStructure.ts](forms.fields.modelFieldStructure.md) — parses the backend's form structures into field types.
- [forms/fields/modelSubfield.ts](forms.fields.modelSubfield.md) — a single form field, its widget, and its subfields.
- [forms/fields/modelMultisubfield.ts](forms.fields.modelMultisubfield.md) — a field holding any number of entries.
- [forms/widgets/widget.ts](forms.widgets.widget.md) — the base class and registry for all widgets.
- [forms/widgets/modelBox.ts](forms.widgets.modelBox.md) — a text input with a filterable dropdown of model choices.
- [forms/widgets/autofillDatacite.ts](forms.widgets.autofillDatacite.md) — a DOI widget that autofills the form.
- [forms/widgets/findIdWidget.ts](forms.widgets.findIdWidget.md) — identifier inputs with a lookup popup.

## Filters

- [filters/filterMenu.ts](filters.filterMenu.md) — the filter menu and its URL syncing.
- [filters/filterMenuItem.ts](filters.filterMenuItem.md) — the selectable items in a filter tab.
- [filters/filterGroup.ts](filters.filterGroup.md) — filter groups and the group maker.
- [filters/filterTab/](filters.filterTab.md) — the filter menu's tabs.
- [filters/search.ts](filters.search.md) — the search bar.

## Model Data

- [modelData/asyncModelData.ts](modelData.asyncModelData.md) — lazy references to model objects.
- [modelData/modelDataCache.ts](modelData.modelDataCache.md) — the client-side cache of model data.
- [modelData/modelStructure.ts](modelData.modelStructure.md) — types for the backend's model names and data shapes.

## Resources

- [resources/resourceItem.ts](resources.resourceItem.md) — the card for one software entry.
- [resources/resourceView.ts](resources.resourceView.md) — the paged list of software entries.

## Dialogues

- [dialogues/apiQueryPopup.ts](dialogues.apiQueryPopup.md) — the base for external-lookup popups.
