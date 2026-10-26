[← Back to Home](index.md)

# Getting Started

A hands-on walkthrough for getting a local HSSI instance running: cloning
the repo, setting environment variables, building the frontend, and
bringing up the Docker stack.

## Contents

- [Prerequisites](#prerequisites)
- [Clone the Repository](#clone-the-repository)
- [Configure .env](#configure-env)
- [Build the Frontend](#build-the-frontend)
- [Launch](#launch)
- [Log In](#log-in)
- [Run the Tests](#run-the-tests)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- **Docker** and **Docker Compose**
- **[bun](https://bun.sh/package-manager)** javascript package manager — `npm` 
will likely also work since `package.json` only declares one dependency, but 
bun is the better bet.

## Clone the Repository

```bash
git clone git@github.com:Heliophysics-Software-Search-Interface/hssi-website.git
```

## Configure .env

Create a `.env` file in the repo root — it's gitignored, so this file
won't exist after a fresh clone and you have to create it yourself.

**Required:**

```
SUPERUSER_NAME="user"
SUPERUSER_PWD="user"
```

These become your Django admin login (see [Log In](#log-in) below).

**Optional**, each unlocking a specific feature:

| Variable | Unlocks |
|---|---|
| `GMAIL_EMAIL`, `GMAIL_APP_PASSWORD` | Outgoing email (submission confirmation / edit-link emails) via Gmail SMTP. Without these, the app still runs — emails just won't send. |
| `GA_MEASUREMENT_ID` | Google Analytics 4. Only renders when `DEBUG` is `False`, so it has no effect on local development either way. |
| `HSSI_UPDATE_TOKEN` | The bearer token required by `PATCH /api/data/software/{id}/` (see [Submission API](api_reference/submission_api.md)). Set this if you want to exercise that endpoint; if it's unset, every PATCH request is rejected. |
| `HSSI_GITHUB_TOKEN` | `python manage.py check_software_versions`, which lists visible software with a newer GitHub release; `--open-issues` also opens an issue in this repository for each one. In production, cron runs `docker exec -w /django HSSI python manage.py check_software_versions --open-issues` daily. Each submission through the submission form opens an issue too, so in local development pass the token to the command alone (`docker exec -e HSSI_GITHUB_TOKEN=… HSSI …`) rather than setting it here. Use a fine-grained token limited to this repository with *Issues: Read and write*, created by an account with write access to it so the issues keep their label. |

## Build the Frontend

The TypeScript frontend is **not** compiled automatically when you run
`docker compose up` — you have to build it yourself first, and re-run the
build any time you change frontend code (there's no watch/hot-reload step).

```bash
bun install
bun run build
```

This runs the `esbuild` script defined in `package.json` and writes the
bundled output to `django/static/js/compiled/hssi-frontend.js`, which the
Docker container picks up via its bind mount — so this must exist before
pages that use it will work correctly, but it doesn't matter whether you
build it before or after `docker compose up` is already running.

Since esbuild can rebuild the frontend in a matter of milliseconds, it is 
often quicker to iterate on frontend development than backend development. 
Just rebuild and refresh the page to test new frontend changes. Contrarily, 
each time a change to the backend is made, the server must be restarted which
takes at least a minute.

## Launch

```bash
docker compose up
```

On first boot (and in fact on every boot — these aren't skipped after the
first run), the container automatically:

- creates the Django project/app scaffolding if it's missing,
- runs `makemigrations` and `migrate`,
- creates your superuser from `SUPERUSER_NAME`/`SUPERUSER_PWD` (via a
  custom `init_superuser` management command — not something you need to
  run yourself),
- runs `collectstatic`,
- and starts Gunicorn behind nginx.

Once it's done, visit `http://localhost` in a browser.

## Log In

Visit `http://localhost/admin/` and log in with the `SUPERUSER_NAME` /
`SUPERUSER_PWD` you set in `.env`.

**The catalog starts completely empty.** There's no seed-data import that
runs automatically — populating the controlled vocabulary (operating
systems, programming languages, instruments, etc.) and any software
records is a manual admin action. See [Code Reference → Admin & Curation](code_reference/admin_and_curation.md); 
for now, expect an empty site immediately after first launch, not a bug.

## Run the Tests

A quick way to confirm the stack is actually working:

```bash
docker exec -w /django HSSI python manage.py test website
```

(`docker-compose.yml` pins the container name to `HSSI`, so this should
work as-is; confirm with `docker ps` if it doesn't.)

## Troubleshooting

- **Static files 403/404 after first launch.** The container writes to the
  bind-mounted `django/static/` directory as a different user than your
  host user, which can leave files unreadable from the host. Run
  `./fix-static-perms.sh` from the repo root to fix permissions.
  *(Noting this as a "try this if it happens" step rather than a required
  one — it wasn't confirmed in this pass how often it's actually needed on
  a typical setup.)*
- **Port 80 already in use.** `docker-compose.yml` maps the container to
  host port 80; if something else on your machine is already bound to it,
  `docker compose up` will fail to bind. Stop the conflicting service or
  change the port mapping locally.
- **Frontend changes not showing up.** Remember the build step isn't
  automatic or watched — re-run `bun run build` after editing anything
  under `frontend/`.
