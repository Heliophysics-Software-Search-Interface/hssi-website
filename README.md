# Heliophysics Software Search Interface (HSSI)

A full stack implementation of the HSSI website source code

HSSI's codebase is derived from the 
[Exoplanet Modeling & Analysis Center (EMAC)](https://emac.gsfc.nasa.gov/)
, which is currently not open-source but is being prepared for release

## Setup

* Clone the repository `git clone https://github.com/Technostalgic/hssi`  
* Ensure environment variables are set in `/.env` (this file is not 
commited to the repository so you will likely need to create it yourself). 
Required environment variables are `SUPERUSER_NAME` and `SUPERUSER_PWD`. Here 
is an example `.env` file:  
```
SUPERUSER_NAME="user"
SUPERUSER_PWD="user"
```
* Start the docker service on your systen and run `docker compose up` in the
project directory.  
* After docker container is fully launched, visit `localhost` in a browser to 
see the website

## Email API

HSSI currently uses gmail smtp to send automated emails through a registered
gmail business account. You will need to provide the following values to the
`.env` file from your own account to utilize the autosending email features:

```
GMAIL_APP_PASSWORD="xxxxxxxxxxxxxxxx"
GMAIL_EMAIL="example@gmail.com"
```

### Compiling

You must first compile the typescript frontend to javascript before running 
the docker container. If you have do not have a package manager, I recommend 
installing [bun](https://bun.sh/package-manager), then restart your terminal
or IDE, and follow the instructions below (if using bun, you'll need to replace 
`npm` in each command with `bun`).

* First you will need to install the dev dependencies required for building.
Assuming you're using npm, use the command `npm install` to install dependencies
from package.json

* After dependencies are finished installing, simply run `npm run build` to 
run the build script for the typescript frontend defined in package.json

## Google Analytics

HSSI uses Google Analytics 4 (GA4) to collect anonymous traffic statistics. To enable it, add your GA4 Measurement ID to the `.env` file:

```
GA_MEASUREMENT_ID="G-XXXXXXXXXX"
```

The analytics tag is only rendered in production (when `DEBUG` is `False`), so local development traffic is never tracked.

## Software Version Checker

The `check_software_versions` management command detects when GitHub-hosted
software listed in HSSI has published a newer release than the version HSSI
currently records. It is adapted from EMAC's `git_fetch_version`, but **defaults
to detection only** — it reports what is out of date and writes nothing unless
you explicitly opt in with `--apply`.

Run it from inside the app container:

```
docker exec HSSI sh -c 'cd /django && python manage.py check_software_versions'
```

Options:

* `--apply` — opt-in; create a new `SoftwareVersion` for each out-of-date entry
  and point the software at it. Off by default (detection only).
* `--csv PATH` — also write the out-of-date report to a CSV file.
* `--limit N` — only check the first N github-hosted software (useful for testing).
* `--github-token TOKEN` — GitHub token for a higher API rate limit. Falls back
  to the `GITHUB_TOKEN` environment variable.

GitHub's anonymous API is limited to 60 requests/hour, which is easily exhausted
on a shared IP (the command will report `HTTP 403/429` rate-limit errors). Supply
a token to raise the limit to 5000 requests/hour:

```
docker exec -e GITHUB_TOKEN=ghp_xxx HSSI sh -c 'cd /django && python manage.py check_software_versions'
```

A token needs no special scopes — read access to public repositories is enough.

Detection rules:

* A software is reported as out-of-date when its repository's highest-numbered
  GitHub release is **strictly newer** than the version HSSI records. An older
  release that was merely published more recently (e.g. a back-ported patch) is
  not treated as an update.
* A software with **no version recorded at all** is also reported, with the latest
  git release suggested as the version to apply.
* Software whose repository has no GitHub releases is counted separately (there is
  nothing to suggest) and is not reported as out-of-date.
