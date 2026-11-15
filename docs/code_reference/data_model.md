[← Back to Code Reference](overview.md)

# Data Model

Reference for the Django model layer: the `HssiModel`/`HssiBase` base
pattern, `ControlledList`/`ControlledGraphList`/`HssiSet`, and the core
`Software`, `SoftwareVersion`, `SubmissionInfo`, `VerifiedSoftware`,
`SoftwareEditQueue`, people/organization, and controlled-vocabulary models.

## Contents

- [Intent](#intent)
- [Base Structure](#base-structure)
  - [HssiBase (Metaclass)](#hssibase-metaclass)
  - [HssiModel](#hssimodel)
  - [ControlledList](#controlledlist)
  - [ControlledGraphList](#controlledgraphlist)
  - [HssiSet](#hssiset)

---

## Intent

The Django Object Relational Model (ORM) is structured such that when changes 
are made to root level objects, they propagate downward effecting all relevant
subtypes. The Tables are treated as classes like you see in Object-Oriented 
Design, and each table that has to do with HSSI software submissions inherits
from the root model `HssiModel`. Further abstractions, `ControlledList` and 
`ControlledGraphList`, are used for general maintained and unmaintained lists.

These Abstractions allow for reusable functionality that is automatically 
integrated into new tables and ensure consistent implementation with other 
tables used in similar ways.

They are also useful for refactoring. Having a inheritance strucure like this 
allows us to refactor a method on a base model whose changes get picked up on 
all inherited models, instead of needing to reimplement the same changes to a 
function on each model manually.

## Base Structure

### [`HssiBase`](../../django/website/models/base.py#L58) (Metaclass)

The HssiBase metaclass allows all HssiModel inherited models to have name 
attributes for each of their django fields, reducing the need to rely on
hardcoded strings to address django fields directly. These string field names
can be referenced with `.name` on the field directly.

#### Example

```py
software_name_fieldname = Software.software_name.name
instance_name_fieldname = Software.objects.first().software_name.name
```

Both of these assignments are set to the same string representing the name of
the `software_name` field in the `Software` model.

### [`HssiModel`](../../django/website/models/base.py#L74)

The abstract base model for all Hssi data models. This base model implements 
simple functionality that we need across all tables. This includes:

- Get the most important field for a model (`get_top_field`)
- Get the 2nd most important field for a model (`get_second_top_field`)
- Internal data serialization and overridable user-facing data serialization
- Other data for improving forms ui such as search terms, choices for dropdown, 
and tooltops

Any new models created for HSSI should inherit from this base model to ensure 
that they work properly with our infrastructure and to ensure consistency 
within the codebase.

### [`ControlledList`](../../django/website/models/base.py#L301)

The abstract base model for all controlled vocabularies, such as programming 
languages, operating systems, and file formats. Each term has a `name`, an optional 
`identifier` URL, and an optional `definition`. This base model implements:

- `name` as the display field, and the default ordering
- The `definition` as the term's tooltip in forms
- Search terms built from the name's words and the identifier
- An optional link to the homepage filtered by the term 
(`homepage_filter_field`)
- A `post_fetch` hook that runs after the vocabulary is fetched from its source

Any new vocabulary that software entries pick terms from should inherit from 
this model, so it works with the existing forms, filters, and vocabulary 
fetching.

### [`ControlledGraphList`](../../django/website/models/base.py#L366)

An extension of `ControlledList` for vocabularies whose terms form a 
parent/child hierarchy, such as regions and software functionality categories. 
Subclasses must define a `children` many-to-many field with 
`related_name='parent_nodes'`. This base model adds:

- A term's full path name, such as `"Parent: Child"` (`get_full_name`)
- Look up a term by its full path name (`get_object_with_full_name`)
- Get all terms that have at least one child (`get_parent_nodes`)
- Repoint references from old terms to new ones and delete the old terms 
(`apply_old_to_new_mapping`)

### [`HssiSet`](../../django/website/models/base.py#L251)

The abstract base model for tables whose rows flag objects of another model, 
such as `VerifiedSoftware` flagging which `Software` entries are publicly 
visible. Each row shares its UUID with the object it flags, set by 
`target_model`. This base model implements:

- Search terms, dropdown choices, and tooltips read from the target object
- Serialized data read from the target object, checked against the set's own 
access level
- A display name taken from the target object's top field

Any new table that marks a subset of another model's entries should inherit 
from this model, so the set's rows can be used anywhere the target object is.
