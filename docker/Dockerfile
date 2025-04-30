FROM python:3.13-slim

LABEL maintainer="isaiah.smith@lasp.colorado.edu"
ENV REFRESHED_AT=2025-01-15

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
RUN chmod +x ./extensions/post-launch-scripts/launch-nginx.sh

ADD launch.sh .
ENTRYPOINT ["sh", "./launch.sh"]

COPY ./requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt
 
# 	pip install django-apptemplates django-colorful django-crispy-forms django-import-export django-ipware django-mathfilters && \
# 	pip install ads analytix gspread oauth2client matplotlib mpld3 nltk numpy pandas requests tweepy vidyo && \
# 	pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2

RUN python -m nltk.downloader -d /usr/local/share/nltk_data stopwords punkt

ADD init_hssi.sh /extensions/django/post-migration-scripts
RUN chmod +x /extensions/django/post-migration-scripts/init_hssi.sh