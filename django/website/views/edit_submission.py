import json, uuid, enum

import django.apps
from django.http import *
from django.shortcuts import render

from ..util import *
from ..models import *

from ..forms import (
	SUBMISSION_FORM_FIELDS_1,
	SUBMISSION_FORM_FIELDS_2,
	SUBMISSION_FORM_FIELDS_3
)

def edit_submission(request: HttpRequest) -> HttpResponse:
	if AccessLevel.from_user(request.user) < AccessLevel.CURATOR:
		return HttpResponseForbidden("You must be a curator to access this page")
	
	return render(
		request, 
		"pages/edit_submission.html", 
		{
			"structure_names": [
				SUBMISSION_FORM_FIELDS_1.type_name,
				SUBMISSION_FORM_FIELDS_2.type_name,
				SUBMISSION_FORM_FIELDS_3.type_name
			],
		}
	)