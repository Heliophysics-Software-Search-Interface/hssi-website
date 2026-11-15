[← Back to Code Reference](overview.md)

# Deployment Reference

Reference for how HSSI is packaged and run: the two Docker Compose services,
the environment variables they read, how the image is built, what happens
when the container starts, and the nginx/Gunicorn configuration in front of
Django. See [Getting Started](../getting_started.md) for the step-by-step
version of running it locally.

## Contents

- [Overview](#overview)
- [Services](#services)
  - [hssi](#hssi)
  - [website_db](#website_db)
- [Environment Variables](#environment-variables)
- [Image Build](#image-build)
  - [Dockerfile](#dockerfile)
  - [Python Dependencies](#python-dependencies)
- [Startup Sequence](#startup-sequence)
  - [launch.sh](#launchsh)
  - [Extension Hooks](#extension-hooks)
- [Server Configuration](#server-configuration)
  - [nginx](#nginx)
  - [Gunicorn](#gunicorn)
  - [Logging](#logging)
- [Applying Changes](#applying-changes)
- [Caveats](#caveats)

---

## Overview

HSSI runs as two Docker containers defined in 
[`docker-compose.yml`](../../docker-compose.yml): one for the website and one
for the PostgreSQL database. The website container runs nginx, Gunicorn, and 
Django together. A request takes this path:

1. nginx receives the request on port `80`.
2. Requests under `/static/` are served directly by nginx from the collected 
static files.
3. Everything else is passed to Gunicorn on port `8000`, which runs Django.
4. Django talks to PostgreSQL over Docker's internal network at host 
`website_db`, port `5432`. The database is not exposed outside that network.

In production, HTTPS is handled by the host's proxy in front of the container, 
so nginx itself only ever serves plain HTTP.

## Services

### [`hssi`](../../docker-compose.yml#L2)

The website container. It's built from [`docker/`](../../docker/Dockerfile), 
tagged `hssi`, named `HSSI`, maps host port `80` to container port `80`, and 
restarts automatically unless stopped by hand. Most of what it runs is mounted 
in from the repo rather than copied into the image:

| Host path | Container path | Contents |
|---|---|---|
| `./django` | `/django` | The Django project source |
| `./django/static` | `/static` | Collected static files, served by nginx |
| `../../logs/nginx` | `/var/log/nginx` | nginx access and error logs |
| `./config/nginx/logrotate` | `/etc/logrotate.d/nginx` | nginx log rotation rules |
| `./config/django` | `/config/django` | Gunicorn and logging config |
| `./config/nginx` | `/etc/nginx/conf.d` | nginx site config |
| `./pip-requirements` | `/extensions/pip-requirements` | Extra pip requirements installed at startup |

Because the source is mounted, code changes don't require rebuilding the 
image, only restarting the container (see [Applying Changes](#applying-changes)).

### [`website_db`](../../docker-compose.yml#L34)

The PostgreSQL container, using the official `postgres` image. Its data is 
kept in the named volume `website_db_data`, so it survives the container 
being stopped or recreated. Docker names the volume after the Compose project 
(by default the repo directory's name), so with a repo directory named `hssi` 
it shows up as `hssi_website_db_data`.

Django connects as user `postgres` to database `postgres`, with 
`SUPERUSER_PWD` as the password (see [Environment Variables](#environment-variables)).

## Environment Variables

Everything the `hssi` container receives, as set in `docker-compose.yml`. 
Values written as `$NAME` are read from the `.env` file in the repo root; the 
rest are fixed in the Compose file.

| Variable | Set in | Used for |
|---|---|---|
| `SUPERUSER_NAME` | `.env` | Username of the Django admin account created at startup |
| `SUPERUSER_PWD` | `.env` | Password of that admin account, **and** the PostgreSQL password for both containers |
| `GMAIL_EMAIL`, `GMAIL_APP_PASSWORD` | `.env` | Sending email through Gmail SMTP; the address is also the sender of every email |
| `HSSI_UPDATE_TOKEN` | `.env` | Bearer token for `PATCH /api/data/software/{id}/` |
| `HSSI_GITHUB_TOKEN` | `.env` | Opening "new submission" GitHub issues, and the `check_software_versions` command |
| `GA_MEASUREMENT_ID` | `.env` | Google Analytics 4 tag, rendered only when `DEBUG` is `False` |
| `PROJECT_NAME` | Compose (`hssi`) | Name of the Django project directory and its WSGI module, used by `launch.sh` |
| `APP_NAME` | Compose (`website`) | Name of the Django app, used by `launch.sh` for migrations |
| `GUNICORN_WORKERS` | Compose (`4`) | Number of Gunicorn worker processes |
| `GUNICORN_BACKLOG` | Compose (`4096`) | Maximum number of pending connections |
| `GUNICORN_BIND` | Compose (`0.0.0.0:8000`) | Address Gunicorn listens on, which nginx proxies to |
| `GUNICORN_TIMEOUT` | Compose (`3600`) | Seconds before an unresponsive worker is restarted |

A few deployment-relevant values are hardcoded in 
[`hssi/settings.py`](../../django/hssi/settings.py) rather than read from the 
environment: `DEBUG` (`False`), `ALLOWED_HOSTS` (the production IP and 
`hssi.hsdcloud.org`), `SECRET_KEY`, and `SITE_DOMAIN`/`SITE_PROTOCOL`.

## Image Build

### [`Dockerfile`](../../docker/Dockerfile)

Builds the website image on top of `python:3.13-slim`. In order, it:

- Installs system packages: build tools and `libpq-dev` for compiling Python 
packages, `nginx`, `git`, `logrotate`, and `procps`
- Installs the base Python packages from `django-requirements.pip`
- Installs [`hssi-somef`](https://github.com/Heliophysics-Software-Search-Interface/hssi-somef), 
HSSI's fork of SOMEF, from its `master` branch, and configures it
- Creates the [extension hook](#extension-hooks) directories under 
`/extensions/`
- Installs `launch-nginx.sh` as a post-launch hook and `launch.sh` as the 
entrypoint
- Installs the pinned Python packages from `requirements.txt`
- Downloads the NLTK `stopwords` and `punkt` data
- Installs `init_hssi.sh` as a post-migration hook

### Python Dependencies

Python packages come from three places:

- [`docker/django-requirements.pip`](../../docker/django-requirements.pip): 
a short, unpinned base set (Django, Gunicorn, the PostgreSQL driver, and JSON 
logging), installed first
- [`docker/requirements.txt`](../../docker/requirements.txt): the full pinned 
set, generated from [`docker/requirements.in`](../../docker/requirements.in) 
with `uv pip compile ./docker/requirements.in -o ./docker/requirements.txt`
- [`pip-requirements/`](../../pip-requirements): extra requirement files 
installed every time the container starts, rather than baked into the image

To add a dependency permanently, add it to `requirements.in`, regenerate 
`requirements.txt`, and rebuild the image.

## Startup Sequence

### [`launch.sh`](../../docker/launch.sh)

The container's entrypoint. It runs every time the container starts, not just 
the first time:

1. Installs each requirements file in `/extensions/pip-requirements/`
2. Runs the pre-launch hooks
3. Creates the Django project and app if `/django/$PROJECT_NAME` is missing 
(never the case with this repo, since the project is committed)
4. Waits one second for the database
5. Runs the pre-migration hooks
6. Runs `makemigrations` for the project and the app, then `migrate`
7. Runs the post-migration hooks, which includes creating the admin account
8. Runs `collectstatic`
9. Runs the post-launch hooks, which includes starting nginx
10. Replaces itself with Gunicorn, which serves Django until the container stops

### Extension Hooks

`launch.sh` runs any executable file placed in these directories at the 
matching point in the startup sequence. This lets a deployment add behavior 
without editing `launch.sh` itself.

| Directory | Runs | Installed by default |
|---|---|---|
| `/extensions/pip-requirements/` | Before everything else (files installed with pip, not executed) | Mounted from `./pip-requirements` |
| `/extensions/pre-launch-scripts/` | Before the Django project check | — |
| `/extensions/django/post-startapp-scripts/` | Only if the Django project had to be created | — |
| `/extensions/django/pre-migration-scripts/` | Before migrations | — |
| `/extensions/django/post-migration-scripts/` | After migrations | [`init_hssi.sh`](../../docker/init_hssi.sh), which runs `python manage.py init_superuser` |
| `/extensions/post-launch-scripts/` | After `collectstatic`, before Gunicorn | [`launch-nginx.sh`](../../docker/launch-nginx.sh), which starts nginx in the background |

## Server Configuration

### [nginx](../../config/nginx/django.conf)

Listens on port `80` for the production IP and `hssi.hsdcloud.org`. It:

- Serves `/static/` directly from `/static/`
- Ignores `/favicon.ico` in the logs
- Proxies every other request to Gunicorn, passing along the original `Host` 
and client IP, and marking the request as HTTPS
- Writes access and error logs to `/var/log/nginx/`, which is mounted to 
`../../logs/nginx` on the host

[`config/nginx/logrotate`](../../config/nginx/logrotate) sets those logs to 
rotate daily and keep 14 compressed days.

### [Gunicorn](../../config/django/gunicorn.conf.py)

`gunicorn.conf.py` turns every `GUNICORN_*` environment variable into the 
matching Gunicorn setting, so `GUNICORN_WORKERS=4` becomes `workers = 4`. To 
change a Gunicorn setting, edit or add the variable in `docker-compose.yml` 
rather than this file.

### [Logging](../../config/django/logging.conf)

Django and Gunicorn log as JSON to standard output, so their logs show up in 
`docker compose logs hssi`. The root logger records `INFO` and above, and 
Gunicorn's error logger records `ERROR` and above.

## Applying Changes

What each kind of change needs before it takes effect:

| Change | Needed |
|---|---|
| Django source, templates | Restart the container (`docker compose restart hssi`) |
| Frontend TypeScript | Rebuild the frontend (`bun run build`); no restart |
| `config/` files, `pip-requirements/` | Restart the container |
| `.env` or `docker-compose.yml` | Recreate the container (`docker compose up -d`) |
| `docker/` (Dockerfile, `requirements.txt`, scripts) | Rebuild the image (`docker compose up -d --build`) |

## Caveats

* Changing `SUPERUSER_PWD` after the database volume exists breaks the 
database connection. PostgreSQL only sets its password the first time the 
volume is initialized, but Django always uses the current value.
* The `postgres` image isn't pinned to a version, so pulling a newer image can 
move to a new PostgreSQL major version, which can't read an older version's 
data without a manual upgrade. CI tests against `postgres:17`.
* `hssi-somef` is installed from its `master` branch, so two builds of the 
image can end up with different versions of it.
* `makemigrations` runs on every startup, so model changes without committed 
migrations get migration files generated inside the mounted `django/` 
directory on whatever machine the container runs on.
* The one-second wait before migrations isn't a readiness check. If the 
database is slow to start, migrations can fail on that boot.
* The nginx log mount `../../logs/nginx` points two directories above the 
repo root, outside the repository.
* [`build-base-image.sh`](../../build-base-image.sh) builds from 
`docker/base_image/`, which doesn't exist in the repo.
