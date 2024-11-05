"""
EMAC ADS Scaper

The purpose of this module is to query the NASA
Astrophysics Data System (ADS) for relevent entries
to be added to EMAC. This is done with a 'narrow' scrape
-- which aims to only find relevent tools, but not all of them
-- and a broad scrape -- which finds all the revelent tools,
but has some non-relevent tools mixed in.

We also don't want to find anything we've found before. To
do this, we save all previously found bibcodes, add them to a
library before each scrape, and specifically exclude that
library from our search. The query syntax to do this is not
very cooperative, so this has to be broken up into multiple
queries in order to achieve the desired behavior (previously,
we had very nice nested queries -- this is not supported by
the current API)
"""

import os
import numpy as np
import pandas as pd

from pathlib import Path
import contextlib
import requests
import json
from json import JSONDecodeError
from urllib.parse import urlencode

import website.admin

from django.conf import settings

API_KEY = settings.ADS_DEV_KEY

ADS_SCRAPER_MODULE_PATH = Path(__file__).parent
BIBCODES_FILE_PATH = os.path.join(ADS_SCRAPER_MODULE_PATH, "bibcodes.csv")
BROAD_RESULTS_FILE_PATH = os.path.join(
    ADS_SCRAPER_MODULE_PATH, "broad_results.csv")
NARROW_RESULTS_FILE_PATH = os.path.join(
    ADS_SCRAPER_MODULE_PATH, "narrow_results.csv")
DB_CONFIG_PATH = website.admin.DEFAULT_DB_CONFIG_PATH
SUBMISSIONS_FILE_PATH = DB_CONFIG_PATH + 'submissions.csv'


@contextlib.contextmanager
def library_context(bibcodes):
    temp_lib_name = "EMAC scraper results"
    payload = {"name": temp_lib_name,
               "description": "This temporary library is created via API",
               "public": False,
               "bibcode": list(bibcodes)}
    results = requests.post("https://api.adsabs.harvard.edu/v1/biblib/libraries",
                            headers={'Authorization': 'Bearer ' + API_KEY},
                            data=json.dumps(payload),timeout=120)
    results = results.json()
    if 'error' in results.keys(): # library already exists
        results = requests.get("https://api.adsabs.harvard.edu/v1/biblib/libraries",
                                headers={'Authorization': 'Bearer ' + API_KEY},timeout=120)
        libraries = results.json()['libraries']
        for library in libraries:
            if library['name'] == temp_lib_name:
                library_to_delete = library['id']
                break
        requests.delete(f"https://api.adsabs.harvard.edu/v1/biblib/documents/{library_to_delete}",
                              headers={'Authorization': 'Bearer ' + API_KEY},timeout=120)
        results = requests.post("https://api.adsabs.harvard.edu/v1/biblib/libraries",
                            headers={'Authorization': 'Bearer ' + API_KEY},
                            data=json.dumps(payload),timeout=120)
        results = results.json()
    library_id = results['id']
    yield library_id
    results = requests.delete(f"https://api.adsabs.harvard.edu/v1/biblib/documents/{library_id}",
                              headers={'Authorization': 'Bearer ' + API_KEY},timeout=120)


def call_api(query, fq=''):
    query = {'q': query,
             'fq': fq,
             "fl": "author, title, abstract, bibcode, date",
             "sort": "date desc",
             "rows": 500}

    encoded_query = urlencode(query)
    results = requests.get("https://api.adsabs.harvard.edu/v1/search/query?{}".format(encoded_query),
                           headers={'Authorization': 'Bearer ' + API_KEY},timeout=120)
    # format the response in a nicely readable format
    return results.json()


def post_query(bibcodes: list):
    encoded_query = urlencode({"q": "*:*",
                               "fl": "author, title, abstract, bibcode, date",
                               "sort": "date desc",
                               "rows": 20
                               })
    bibstring = '\n'.join(bibcodes)
    payload = f"bibcode\n{bibstring}"
    results = requests.post("https://api.adsabs.harvard.edu/v1/search/bigquery?{}".format(encoded_query),
                            headers={'Authorization': 'Bearer ' + API_KEY},
                            data=payload,timeout=120)

    return results.json()


def scrape():
    try:
        known_bibcodes = pd.read_csv(BIBCODES_FILE_PATH).bibcode.values
    except FileNotFoundError:
        known_bibcodes = np.array([], dtype='str')
    software_content_keys = ['machine learning', 'object oriented', 'code', 'python', 'fortran', 'matlab',
                             'toolkit', 'pipeline']
    software_availability_keys = ['github', 'zenodo', '=package', 'community', 'open-source', 'public release',
                                  'we present']
    bibstems = ['joss', 'ascl', 'zndo']

    with library_context(known_bibcodes) as library_id:
        base_query = f"collection:astronomy abs:exoplanet -docs(library/{library_id})"
        print('Initiating Narrow Scraper')
        def narrow():
            bibcodes = []
            num_found = 0
            for content_key in software_content_keys:
                if (' ' in content_key) or ('=' in content_key):
                    content_key = f'"{content_key}"'
                for availability_key in software_availability_keys:

                    if (' ' in availability_key) or ('=' in availability_key):
                        availability_key = f'"{availability_key}"'
                    fq = f'abs:{content_key} and abs:{availability_key}'
                    print(f'Filter query: {fq}')
                    try:
                        results = call_api(base_query, fq=fq)
                        try:
                            response = results['response']
                            num_found += response['numFound']
                            for doc in response['docs']:
                                if doc['bibcode'] not in bibcodes:
                                    bibcodes.append(doc['bibcode'])
                        except KeyError:
                            print(f'error for fq={fq}')
                            print(results)
                    except JSONDecodeError:
                        print(f'Could not decode with fq={fq}, possible server-side timeout')
            for key in bibstems:
                fq = f'bibstem:{key}'
                print(f'Filter query: {fq}')
                try:
                    results = call_api(base_query, fq=fq)
                    try:
                        response = results['response']
                        num_found += response['numFound']
                        for doc in response['docs']:
                            if doc['bibcode'] not in bibcodes:
                                bibcodes.append(doc['bibcode'])
                    except KeyError:
                        print(f'fq={fq}')
                        print(results)
                except JSONDecodeError:
                    print(f'Could not decode with fq={fq}')

            results = post_query(bibcodes)
            try:
                response = results['response']
            except KeyError as err:
                print(results)
                raise err
            print(f'found {num_found}, including {len(bibcodes)} unique')
            return response['docs']
        narrow_results = narrow()
        narrow_df = pd.DataFrame(narrow_results)
        narrow_df.loc[:,'title'] = narrow_df['title'].apply(lambda x: x[0])
        narrow_df['link'] = 'https://ui.adsabs.harvard.edu/abs/' + \
            narrow_df['bibcode'].astype('str') + '/abstract'
        known_bibcodes = np.append(known_bibcodes, narrow_df.bibcode.values)
        narrow_df = narrow_df[['date','author','title','abstract','bibcode','link']]
        narrow_df.to_csv(NARROW_RESULTS_FILE_PATH, index=False)

    with library_context(known_bibcodes) as library_id:
        base_query = f"collection:astronomy abs:exoplanet -docs(library/{library_id})"
        print('Initiating Broad Scraper')
        def broad():
            bibcodes = []
            num_found = 0
            for key in software_content_keys + software_availability_keys:
                if (' ' in key) or ('=' in key):
                    key = f'"{key}"'
                fq = f'abs:{key}'
                print(f'Filter query: {fq}')
                try:
                    results = call_api(base_query, fq=fq)
                    try:
                        response = results['response']
                        num_found += response['numFound']
                        for doc in response['docs']:
                            if doc['bibcode'] not in bibcodes:
                                bibcodes.append(doc['bibcode'])
                    except KeyError:
                        print(f'fq={fq}')
                        print(results)
                except JSONDecodeError:
                    print(f'Could not decode with fq={fq}, possible server-side timeout')

            results = post_query(bibcodes)
            try:
                response = results['response']
            except KeyError as err:
                print(results)
                raise err
            print(f'found {num_found}, including {len(bibcodes)} unique')
            return response['docs']
        broad_results = broad()
        broad_df = pd.DataFrame(broad_results)
        broad_df.loc[:,'title'] = broad_df['title'].apply(lambda x: x[0])
        broad_df['link'] = 'https://ui.adsabs.harvard.edu/abs/' + \
            broad_df['bibcode'].astype('str') + '/abstract'
        known_bibcodes = np.append(known_bibcodes, broad_df.bibcode.values)
        broad_df = broad_df[['date','author','title','abstract','bibcode','link']]
        broad_df.to_csv(BROAD_RESULTS_FILE_PATH, index=False)
    pd.DataFrame({'bibcode': known_bibcodes}).to_csv(
        BIBCODES_FILE_PATH, index=False)
