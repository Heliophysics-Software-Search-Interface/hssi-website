# Heliophysics Software Search Interface (HSSI)

A full stack implementation of the HSSI website source code

## Setup

* Clone the repository `git clone https://github.com/Technostalgic/hssi`  
* Ensure environment variables are set in `/EMAC/.env` (this file is not 
commited to the repository so you will likely need to create it yourself). 
Required environment variables are `POSTGRES_USER`, `POSTGRES_PASSWORD`, 
`POSTGRES_DB`, `EMAC_ADMIN_USERNAME`, `EMAC_ADMIN_PASSWORD`, `SECRET_KEY`. 
The values can be filled with any string literals, ex: `POSTGRESS_USER="user"`.
* Start the docker service on your systen and run `docker compose up` in the
`/EMAC/` directory.  
* Visit `localhost` in a browser to see the website