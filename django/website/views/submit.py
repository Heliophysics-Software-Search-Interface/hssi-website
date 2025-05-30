from django.shortcuts import render, HttpResponse
from ..forms import (
    SUBMISSION_FORM_FIELDS_1,
    SUBMISSION_FORM_FIELDS_2,
    SUBMISSION_FORM_FIELDS_3,
    SUBMISSION_FORM_FIELDS_AGREEMENT,
)

def submit_resource(request):
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
