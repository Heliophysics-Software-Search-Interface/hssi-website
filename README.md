# Heliophysics Software Search Interface (HSSI)

A full stack implementation of the HSSI website source code

HSSI's codebase is derived from the 
[Exoplanet Modeling & Analysis Center (EMAC)](https://emac.gsfc.nasa.gov/)
, which is currently not open-source but is being prepared for release

## Setup

* Clone the repository `git clone https://github.com/Technostalgic/hssi`  
* Ensure environment variables are set in `/.env` (this file is not 
commited to the repository so you will likely need to create it yourself). 
Required environment variables are `POSTGRES_USER`, `POSTGRES_PASSWORD`, 
`POSTGRES_DB`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `SECRET_KEY`. Here 
is an example `.env` file:  
```
POSTGRES_USER="user"
POSTGRES_PASSWORD="user"
POSTGRES_DB="db"
ADMIN_USERNAME="user"
ADMIN_PASSWORD="user"
SECRET_KEY="secret"
```
* Start the docker service on your systen and run `docker compose up` in the
project directory.  
* After docker container is fully launched, visit `localhost` in a browser to 
see the website