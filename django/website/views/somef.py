import subprocess, json, uuid

from django.http import response, request

def describe_view(req: request.HttpRequest):
    
    tempfname = "/" + str(uuid.uuid4()) + ".json"

    # run the somef command to extract metadata
    process = subprocess.run(["somef", "describe", "-t", "0.7", "-r", (
            req.GET.get(
                "target", 
                "https://github.com/Heliophysics-Software-Search-Interface/hssi-website")
        ), "-o", tempfname],
    )

    # parse the data from somef to JSON data
    process = subprocess.run(["cat", tempfname], stdout=subprocess.PIPE)
    data = json.loads(process.stdout.decode('utf-8'))

    # remove the temporary file
    subprocess.run(["rm", tempfname])

    return response.JsonResponse(data)