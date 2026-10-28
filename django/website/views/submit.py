import json, uuid, datetime
from uuid import UUID

from django.conf import settings
from django.utils import timezone
from django.shortcuts import render, redirect, HttpResponse
from django.db import transaction
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
from .. import github
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

	with transaction.atomic():
		# try handle json_data and save to database
		print("recieved form submission..")
		submisison_id = handle_submission_data(json_data)
		software: Software = SubmissionInfo.objects.get(pk=submisison_id).software
		print("submitted!")

		# mark for review edits
		SoftwareEditQueue.create(software, timezone.now() + datetime.timedelta(days=90))
		transaction.on_commit(lambda: open_submission_issue(software), robust=True)
		transaction.on_commit(lambda s=software: [
			email_existing_edit_link(si) for si in s.submission_info.all()
		])

	return redirect(f"/submit/submitted/?uid={str(software.pk)}")

def open_submission_issue(software: Software) -> None:
	"""Open a "new submission" GitHub issue that names the software and shows no other submitted values."""
	if not settings.HSSI_GITHUB_TOKEN:
		return
	github.open_issue(
		f"New submission: {software.software_name}",
		"Submitted through the HSSI submission form. Someone should go review it now.",
		"new submission",
	)
