import json, uuid, enum

from django.core.mail import send_mail
from django.http import *
from django.shortcuts import render

from .submit import handle_submission_data
from ..util import *
from ..models import *

from ..forms import (
	SUBMISSION_FORM_FIELDS_1,
	SUBMISSION_FORM_FIELDS_2,
	SUBMISSION_FORM_FIELDS_3
)

def request_edit_link(request: HttpRequest, uid: str) -> HttpResponse:
	if request.method != "POST": return HttpResponseBadRequest("expected POST")
	try:
		test_email = request.body.decode("utf-8").lower()
		if len(test_email) <= 0: return HttpResponseBadRequest()
		id = uuid.UUID(uid)
		software = Software.objects.get(pk=id)
		correct_emails: list[str] = software.submissionInfo.submitter.email_list()
		for correct_email in correct_emails:
			if test_email == correct_email.lower():
				email_edit_link(software.submissionInfo)
				return HttpResponse(status=204)
		return HttpResponseBadRequest("Incorrect email")

	except Exception: return HttpResponseServerError()

def get_submission_data(request: HttpRequest, uid: str) -> HttpResponse:
	queue_item: SoftwareEditQueue = None

	try:
		queue_item = SoftwareEditQueue.objects.get(pk=uuid.UUID(uid))
	except Exception:
		return HttpResponseBadRequest("Invalid uid or object does not exist")

	if queue_item.is_expired():
		# queue_item.delete()
		return HttpResponseBadRequest("Submission edit link has expired")

	data = queue_item.target_software.get_serialized_data(AccessLevel.CURATOR, True)
	return JsonResponse(data)

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

def submit_edits(request: HttpRequest, uid: str) -> HttpResponse:
	queue_item: SoftwareEditQueue = None

	try:
		queue_item = SoftwareEditQueue.objects.get(pk=uuid.UUID(uid))
	except Exception:
		return HttpResponseBadRequest("Invalid uid or object does not exist")

	if queue_item.is_expired():
		# queue_item.delete()
		return HttpResponseBadRequest("Submission edit link has expired")

	try:
		encoding = request.encoding or "utf-8"
		data = request.body.decode(encoding)
		json_data = json.loads(data)
		handle_submission_data(json_data, queue_item.target_software)

	except Exception: return HttpResponseServerError()
	return HttpResponse(status=204)

def email_edit_link(submission: SubmissionInfo):
	queue_item = SoftwareEditQueue.create(submission.software)
	link = f"https://hssi.hsdcloud.org/curate/edit_submission/?uid={str(queue_item.id)}"
	emails = submission.submitter.email_list()
	print(f"Sending edit links for {queue_item.id} to {emails}...")
	send_mail("[HSSI] Edit Submission", link, None, emails)