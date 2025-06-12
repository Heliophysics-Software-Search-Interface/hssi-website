import subprocess, json, uuid, urllib.parse
from difflib import SequenceMatcher
import dateutil.parser
from packaging import version
import re

from django.http import response, request

from ..forms import names, submission_data

def describe_view(req: request.HttpRequest) -> response.JsonResponse:
    
    tempfname = "/" + str(uuid.uuid4()) + ".json"
    output_fmt = "-" + req.GET.get("fmt", "o")
    target = req.GET.get(
        "target", 
        "https://github.com/Heliophysics-Software-Search-Interface/hssi-website"
    )
    target = urllib.parse.unquote(target)

    # run the somef command to extract metadata
    process = subprocess.run(
        ["somef", "describe", "-t", "0.7", "-r", target, output_fmt, tempfname],
        stdout=subprocess.PIPE,
    )

    # parse the data from somef to JSON data
    process = subprocess.run(["cat", tempfname], stdout=subprocess.PIPE)
    data = json.loads(process.stdout.decode('utf-8'))

    # remove the temporary file
    subprocess.run(["rm", tempfname])

    return response.JsonResponse(data, content_type="application/ld+json")

def form_fill_view(req: request.HttpRequest) -> response.HttpResponse:
    return response.HttpResponse(
        json.dumps(
            somef_to_formdict(
                json.loads(describe_view(req).content.decode('utf-8'))
            )
        ),
        content_type="application/json"
    )

def somef_to_formdict(data: dict) -> dict:
    """
    converts all fields in the specified codemeta json ld dict, to a dict
    that is compatible for filling out the submission form fields
    """
    formdict = {}
    confidence = 0

    # search for identifier field
    data_id = data.get("identifier", [])
    for entry in data_id:
        result = entry.get("result", None)
        if result:
            formdict[names.FIELD_PERSISTENTIDENTIFIER] = result.get("value", "")
    
    # search for authors
    form_authors = []
    data_authors = data.get("authors", [])
    for entry in data_authors:
        result = entry.get("result", {})
        if result:
            author = {}
            author[names.FIELD_AUTHORS] = result.get("name", "")
            author[names.FIELD_AUTHORIDENTIFIER] = result.get("url", "")
            form_authors.append(author)
    if form_authors: formdict[names.FIELD_AUTHORS] = form_authors
    
    # search for software name
    data_title = data.get("full_title", [])
    form_title = None
    confidence = 0
    for entry in data_title:
        result = entry.get("result", None)
        res_conf = entry.get("confidence", 0)
        if res_conf > confidence and result:
            val = result.get("value", None)
            if val: 
                form_title = val
                confidence = res_conf
    if not form_title:
        confidence = 0
        data_name = data.get("name", [])
        for entry in data_name:
            result = entry.get("result", None)
            res_conf = entry.get("confidence", 0)
            if result and res_conf > confidence:
                val = result.get("value", None)
                if val:
                    form_title = val
                    confidence = res_conf
    if form_title: formdict[names.FIELD_SOFTWARENAME] = form_title

    # search for description
    data_desc = data.get("description", [])
    form_desc = ""
    confidence = 0
    for entry in data_desc:
        result = entry.get("result", None)
        res_conf = entry.get("confidence", 0)
        if result and res_conf >= confidence:
            val = result.get("value", None)
            if val:
                # if the descriptions have similar confidence
                if abs(res_conf - confidence) < 0.02:
                    # use the more confident choice them if they are similar,
                    # otherwise combine them together
                    similarity = SequenceMatcher(None, form_desc, val).ratio()
                    if similarity > 0.8: 
                        form_desc = val if res_conf > confidence else form_desc
                    else: form_desc += "\n" + val
                    confidence = max(res_conf, confidence)
                else: 
                    form_desc = val
                    confidence = res_conf
    if form_desc: formdict[names.FIELD_DESCRIPTION] = form_desc

    # search for publication date
    data_pubdate = data.get("date_created", [])
    form_pubdate = None
    confidence = 0
    for entry in data_pubdate:
        result = entry.get("result", None)
        res_conf = entry.get("confidence", 0)
        if result and res_conf >= confidence:
            val = result.get("value", None)
            if val:
                form_pubdate = val
                confidence = res_conf
    if form_pubdate:
        date = dateutil.parser.parse(form_pubdate)
        form_pubdate = date.strftime("%Y-%m-%d")
        formdict[names.FIELD_PUBLICATIONDATE] = form_pubdate

    # Publisher - not enough info

    # Version
    data_version = data.get("version", [])
    form_version: version.Version = None
    for entry in data_version:
        result = entry.get("result", None)
        if result:
            val = result.get("value", None)
            if val:
                # choose the newest version
                if not form_version: form_version = version.parse(val)
                else: form_version = max(form_version, version.parse(val))
    if form_version:
        formdict[names.FIELD_VERSIONNUMBER] = {
            names.FIELD_VERSIONNUMBER: str(form_version),
        }

        # Version Date
        data_verdate = data.get("date_updated", [])
        form_verdate = None
        confidence = 0
        for entry in data_verdate:
            result = entry.get("result", None)
            res_conf = entry.get("confidence", 0)
            if result and res_conf >= confidence:
                val = result.get("value", None)
                if val:
                    form_verdate = val
                    confidence = res_conf
        if form_verdate: 
            date = dateutil.parser.parse(form_verdate)
            form_verdate = date.strftime("%Y-%m-%d")
            formdict[names.FIELD_VERSIONNUMBER][names.FIELD_VERSIONDATE] = form_verdate

    # Programming Languages
    data_proglangs = data.get("programming_languages", [])
    form_proglangs = []
    for entry in data_proglangs:
        result = entry.get("result", None)
        if result:
            val = result.get("value", None)
            if val:
                match val:
                    case "Jupyter Notebook": continue
                    case "Python": val = "Python 3.x"
                form_proglangs.append(val)
    if form_proglangs: formdict[names.FIELD_PROGRAMMINGLANGUAGE] = form_proglangs

    # Licence
    data_license = data.get("license", [])
    form_license = None
    confidence = 0
    for entry in data_license:
        result = entry.get("result", None)
        res_conf = entry.get("confidence", 0)
        if(result):
            val = result.get("value", None)
            if val and res_conf >= confidence:
                # choose the most confident license
                id = result.get("spdx_id", "")
                if not id: id = result.get("name", "")
                if id:
                    form_license = id
                    confidence = res_conf
    if form_license: formdict[names.FIELD_LICENSE] = form_license

    # Keywords
    data_keywords = data.get("keywords", [])
    form_keywords = []
    for entry in data_keywords:
        result = entry.get("result", None)
        if result:
            val: str = result.get("value", None)
            if val:
                vals = map(lambda x: x.strip(), val.split(","))
                vals = filter(lambda x: len(x) > 0, vals)
                form_keywords.extend(vals)
    if form_keywords: formdict[names.FIELD_KEYWORDS] = form_keywords

    # Software Functionality - not enough info
    # Data Inputs - not enough info
    # Supported File Formats - not enough info
    # Operating System - not enough info
    # Related Region - not enough info

    # Reference Publications

    # Development Status
    data_devstatus = data.get("repository_status", [])
    form_devstatus = None
    confidence = 0
    for entry in data_devstatus:
        result = entry.get("result", None)
        res_conf = entry.get("confidence", 0)
        if result and res_conf >= confidence:
            val = result.get("description", None)
            if val:
                # choose the most confident development status
                form_devstatus = val.strip().split(" ")[0].strip()
                confidence = res_conf
    if form_devstatus: formdict[names.FIELD_DEVELOPMENTSTATUS] = form_devstatus

    # Documentation (link)
    data_docs = data.get("documentation", [])
    form_docs = None
    confidence = 0
    for entry in data_docs:
        result = entry.get("result", None)
        res_conf = entry.get("confidence", 0)
        if result:
            val = result.get("value", None)
            if val: 
                val = get_url_fromstr(val)
                if val:
                    # we want to prioritize links that don't point to the repo
                    override = not not form_docs
                    underride = False
                    exc_domains = [
                        "github.com", 
                        "githubusercontent.com", 
                        "gitlab.com"
                    ]
                    for domain in exc_domains:
                        override = override and domain in form_docs
                        underride = underride or domain in val
                    if (res_conf > confidence or override) and not underride:
                        form_docs = val
                        confidence = res_conf
    if form_docs: formdict[names.FIELD_DOCUMENTATION] = form_docs

    # Funder - not enough info
    # Awards - not enough info

    # Related Publications - not enough info
    # Related Datasets - not enough info
    # Related Software - not enough info
    # Interoperable Software - not enough info
    # Related Instruments - not enough info
    # Related Observatories - not enough info

    # Logo
    data_logo = data.get("logo", [])
    form_logo = None
    confidence = 0
    for entry in data_logo:
        result = entry.get("result", None)
        res_conf = entry.get("confidence", 0)
        if result and res_conf > confidence:
            val = result.get("value", None)
            if val:
                val = get_url_fromstr(val)
                if val:
                    form_logo = val
                    confidence = res_conf
    if form_logo: formdict[names.FIELD_LOGO] = form_logo

    return formdict

def get_url_fromstr(string: str) -> str:
    """
    extracts a valid URL from the given string
    """
    url_regex = r'https?:\/\/[^\s\]\)]+'
    match = re.search(url_regex, string)
    if match: 
        return match.group(0)
    return ""