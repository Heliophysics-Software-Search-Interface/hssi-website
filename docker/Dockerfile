FROM hssi

LABEL maintainer="isaiah.smith@lasp.colorado.edu"
ENV REFRESHED_AT=2021-07-14

COPY ./requirements.txt requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt
 
# 	pip install django-apptemplates django-colorful django-crispy-forms django-import-export django-ipware django-mathfilters && \
# 	pip install ads analytix gspread oauth2client matplotlib mpld3 nltk numpy pandas requests tweepy vidyo && \
# 	pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2

RUN python -m nltk.downloader -d /usr/local/share/nltk_data stopwords punkt

ADD init_emac.sh /extensions/django/post-migration-scripts
RUN chmod +x /extensions/django/post-migration-scripts/init_emac.sh