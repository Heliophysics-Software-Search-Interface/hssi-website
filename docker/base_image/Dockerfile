FROM python:3.10-slim

LABEL maintainer="isaiah.smith@lasp.colorado.edu"

ENV REFRESHED_AT=2021-10-07

ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get -y install gcc libpq-dev logrotate procps && \
    rm -rf /var/lib/apt/lists/*

ADD django-requirements.pip .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r django-requirements.pip

RUN apt-get update && \
    apt-get install -y nginx

WORKDIR /extensions/pip-requirements
WORKDIR /extensions/pre-launch-scripts
WORKDIR /extensions/django/post-startapp-scripts
WORKDIR /extensions/django/pre-migration-scripts
WORKDIR /extensions/django/post-migration-scripts
WORKDIR /extensions/post-launch-scripts

WORKDIR /

ADD launch-nginx.sh ./extensions/post-launch-scripts/

ADD launch.sh .
CMD ./launch.sh