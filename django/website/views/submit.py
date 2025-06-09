import json

from django.shortcuts import render, HttpResponse
from django.http import HttpRequest, HttpResponseBadRequest, JsonResponse
from ..forms import (
    SUBMISSION_FORM_FIELDS_1,
    SUBMISSION_FORM_FIELDS_2,
    SUBMISSION_FORM_FIELDS_3,
    SUBMISSION_FORM_FIELDS_AGREEMENT,
)

def submit_resource(request: HttpRequest) -> HttpResponse:
    return render(
        request, 
        "pages/submit.html", 
        { 
            "structure_names": [
                SUBMISSION_FORM_FIELDS_1.type_name,
                SUBMISSION_FORM_FIELDS_2.type_name,
                SUBMISSION_FORM_FIELDS_3.type_name,
                SUBMISSION_FORM_FIELDS_AGREEMENT.type_name,
            ],
        }
    )

def submit_post(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("POST expected")
    
    # parse request body to json
    encoding = request.encoding or "utf-8"
    data = request.body.decode(encoding)
    json_data = json.loads(data)

    return JsonResponse(json_data)
