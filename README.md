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