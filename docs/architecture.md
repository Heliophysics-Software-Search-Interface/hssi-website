[← Back to Home](index.md)

# Architecture

High level overview of how the system is put together - the Django backend, 
the progressive-enhancement TypeScript frontend, and the services around them - 
and the design rationale behind the handful of deliberate, non-obvious patterns
(`HssiModel`, controlled vocabularies, the shared frontend/backend form
schema, and the publish/verification model) that a newcomer would
otherwise have to reverse-engineer from the code.

## Contents

- [Backend](#backend)
- [Frontend](#frontend)
- [Object Relational Mapping (ORM) Design](#object-relational-mapping-orm-design)
- [Submission lifecycle](#submission-lifecycle)

---

### Backend

The server is written in python with the 
[Django](https://www.djangoproject.com/) framework with a relational 
PostgreSQL database. Initial databse structure followed 
[this model](../concept/db_structure.dbm), but has since diverged as we've
made migrations.

The Django codebase runs on and gunicorn, and is served by nginx. The current
host, [NASA's heliocloud](https://github.com/heliocloud-data), provides a 
proxy which allows site traffic to be encrypted through https without needing 
a signed cert specifically for HSSI.

The server and PostgreSQL each run in separate Docker containers, and the 
server interacts with the database over the default PostgreSQL port, `5432`. 
The database is not exposed except to the server through Docker's network.

### Frontend

The site's frontend is written in typescript, compiled manually with esbuild 
(see [script defined in package.json](../package.json#L12)). 

The design was meant to transition from the django html template files used in 
EMAC, into a more dynamically generated html, from data retrieved by ajax/fetch 
requests through the REST API, but I only got about halfway through that 
transition, so it's a bit messy. Going forward, any new code should try to 
align with this philosophy of requesting content through the api, then 
generating html for it through the frontend.

Barrel imports - all imports happen from and through the 
[loader](../frontend/loader.ts) module (though this was never meant to be 
permenant, so should probably change in the future).

### Object Relational Mapping (ORM) Design

Every model inherits from [HssiModel](../django/website/models/base.py#L54), 
which homogenizes a default interface
to allow for highly generic and reusable functionality. This base class 
provides a consistent way to form unique identifiers for database entries, and
sets up a model-wide access level and serialization methods that can be 
overriden for quick but extensible additions or modifications to models.

The [ControlledList](../django/website/models/base.py#L255) defines a generic 
shape for a data list. This structure allows for consistent implementation of 
searching and filtering for software entries in the database among a diverse 
set of subfields. Also, because the data list's shape is known, functionality 
exists to easily implement fetching data from an external source, examples of 
which can be seen with these controlled vocabularies:

* [Region](../django/website/admin/fetch_vocab.py#L47)
* [ProgrammingLanguages](../django/website/admin/fetch_vocab.py#L44)
* [RepoStatus](../django/website/admin/fetch_vocab.py#L46)
* [InstrumentObservatory](../django/website/admin/fetch_vocab.py#L240)

The [Structurizer](../django/website/models/structurizer.py) module allows 
these models to be described as data, which then allows forms to be generated 
dynamically from this structure. Since these structures represent the database 
relations, they can be used to interact with or modify data on the frontend, 
through dynamic HTML forms.

### Submission lifecycle

The main purpose of the site is to collect software for heliophysics and 
provide a layer of metadata interoperability and discovery for them. In order
to do that we need submissions, but those submissions must be curated, 
filterable, searchable, and have relevant information that users are 
interested in. This is an overview of how that's supposed to work:

1. A software maintainer navigates to the submission page, fills out the 
relevant form fields, and submits it.  
2. The data in the form is serialized and sent to the HSSI [Software](../django/website/models/software.py#L71) 
model in our database. A confirmation email is sent to the email address the
maintainer entered.
3. A curator reviews the data in the software entry and reaches out to the 
submitter email if any modifications need to be made.
4. After all data is verified, and no more modifications are needed, a curator
'verifies' the software entry. Its UUID is added to the [VerifiedSoftware](../django/website/models/software.py#L341) 
model and, as a result, it becomes visible on the HSSI website.
5. If an author needs to make a correction after it has been verified, they 
can select an option on the software's landing page, which prompts them to
verify they are the original submitter by reentering their email address. A 
unique edit link is sent to their email if it matches.

This is meant to be a low-friction barrier for submission, since there is no
need for a software submitter to create an account.

**Caveats**:

* There is an [internal status field](../django/website/models/software.py#L310) 
in each software entry, but it is currently unused as we have no way to 
consistently track progress for each entry.
* Limited access curator roles do not currently exist, despite some of the 
foundation for it being in place. Curation is done by website admins.  
* We currently have no way to verify the submitter of a given software actually
has any relation to it.  
* There is currently no additional verification required for edits made after 
an entry is already verified.  

Additionally, there is an api endpoint which allows to make multiple 
submissions at once, following 
[the submission example](../concept/import_submission.json) json structure. 
This is useful for site interoperaibility or if you would like to submit many 
entries at once from another repository or database.