#!/usr/bin/env bash

docker-compose -f docker-compose.prod.yml -f docker-compose.yml up -d
