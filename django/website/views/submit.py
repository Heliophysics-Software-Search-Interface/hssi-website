import json, uuid, datetime
from uuid import UUID

from django.utils import timezone
from django.shortcuts import render, redirect, HttpResponse
from django.http import (
	HttpRequest, HttpResponseBadRequest, 
	JsonResponse, HttpResponseRedirect, HttpResponseServerError,
)

from ..forms import (
	SUBMISSION_FORM_FIELDS_1,
	SUBMISSION_FORM_FIELDS_2,
	SUBMISSION_FORM_FIELDS_3
)
from ..models import *
from ..forms.names import *
from ..util import *
from ..data_parser import handle_submission_data
from .edit_submission import email_existing_edit_link

def view_form(request: HttpRequest) -> HttpResponse:
	return render(
		request, 
		"pages/submit.html", 
		{ 
			"structure_names": [
				SUBMISSION_FORM_FIELDS_1.type_name,
				SUBMISSION_FORM_FIELDS_2.type_name,
				SUBMISSION_FORM_FIELDS_3.type_name
			],
		}
	)

def view_confirmation(request: HttpRequest) -> HttpResponse:
	if request.method != "GET":
		return HttpResponseBadRequest("GET expected")
	
	return render(
		request,
		"pages/submit_confirmation.html",
		{ "recieved_data": request.body }
	)

def submit_data(request: HttpRequest) -> HttpResponse:
	if request.method != "POST":
		return HttpResponseBadRequest("POST expected")
	
	# parse request body to json
	encoding = request.encoding or "utf-8"
	data = request.body.decode(encoding)
	json_data = json.loads(data)

	# try handle json_data and save to database
	print("recieved form data", json_data)
	submisison_id = handle_submission_data(json_data)
	software: Software = SubmissionInfo.objects.get(pk=submisison_id).software

	# mark for review edits
	SoftwareEditQueue.create(software, timezone.now() + datetime.timedelta(days=90))
	email_existing_edit_link(software.submissionInfo)

	return redirect(f"/submit/submitted/?uid={str(software.pk)}")
