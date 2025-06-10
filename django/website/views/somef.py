import subprocess, json

from django.http import response, request

def describe_view(req: request.HttpRequest):
    
    process = subprocess.run(["somef", "describe", "-r", (
            req.GET.get(
                "target", 
                "https://github.com/Heliophysics-Software-Search-Interface/hssi-website")
        ), "-o", "/test.json"]
    )
    process = subprocess.run(["cat", "/test.json"], stdout=subprocess.PIPE)

    return response.JsonResponse({"value": process.stdout.decode('utf-8')})