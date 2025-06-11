import subprocess, json, uuid, urllib.parse

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
        json.dumps(codemeta_to_formdict(json.loads(describe_view(req).content))),
        content_type="application/json"
    )

def codemeta_to_formdict(data: dict) -> dict:
    """
    converts all fields in the specified codemeta json ld dict, to a dict
    that is compatible for filling out the submission form fields
    """
    formdict = {}

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
        form_entry = {}
        result = entry.get("result", {})
        form_entry[names.FIELD_AUTHORS] = result.get("name", "")
        form_entry[names.FIELD_AUTHORIDENTIFIER] = result.get("url", "")
        form_authors.append(form_entry)
    formdict[names.FIELD_AUTHORS] = form_authors

    # search for software name field
    data_swname = data.get("name", [])
    for entry in data_swname:
        result = entry.get("result", None)
        if result:
            val = result.get("value", None)
            if val:
                formdict[names.FIELD_SOFTWARENAME] = val
                break
    
    # search for description
    data_desc = data.get("description", [])
    form_desc = ""
    for entry in data_desc:
        result = entry.get("result", None)
        if result:
            val = result.get("value", None)
            if val and len(val) > len(form_desc):
                form_desc = val
    if len(form_desc) > 0:
        formdict[names.FIELD_DESCRIPTION] = form_desc

    # TODO the rest of the fields

    return formdict
