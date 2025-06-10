import subprocess, json, uuid, urllib.parse

from django.http import response, request

def describe_view(req: request.HttpRequest):
    
    tempfname = "/" + str(uuid.uuid4()) + ".json"
    output_fmt = "-" + req.GET.get("fmt", "c")
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

    return response.JsonResponse(data)