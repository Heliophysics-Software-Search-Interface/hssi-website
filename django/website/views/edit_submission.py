import json, uuid, enum

from django.core.mail import send_mail
from django.http import *
from django.shortcuts import render

from ..data_parser import handle_submission_data
from ..util import *
from ..models import *

from ..forms import (
	SUBMISSION_FORM_FIELDS_1,
	SUBMISSION_FORM_FIELDS_2,
	SUBMISSION_FORM_FIELDS_3
)

def request_edit_link(request: HttpRequest, uid: str) -> HttpResponse:
	""" http view for requesting an edit link to a given software uid """
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

def email_existing_edit_link(submission: SubmissionInfo) -> bool:
	"""
	grabs an edit link from the software edit queue whose expiration date is 
	the furthest away and emails that to the submitter in the submission info,
	returns false if no edit link exists
	"""
	items = SoftwareEditQueue.objects.filter(target_software=submission.software)
	item = items.first()
	if not item: return False
	

	# find latest expiring item
	for i in items: 
		if i.expiration > item.expiration: item = i
	
	user: Person = submission.submitter.person
	software: Software = submission.software
	emails = submission.submitter.email_list()
	link = f"https://hssi.hsdcloud.org/curate/edit_submission/?uid={str(item.id)}"

	message = (
		f"Hello {user.firstName}, \n\n" +
		f"Thank you for submitting your software to HSSI. Once your submission " +
		f"is reviewed, a curator will contact you at this email.\n" +
		f"In the meantime, you can view or edit your submission with the " +
		f"link below: \n\n{link}\n\n" +
		f"Please do not share this link publicly, as anyone with this link " +
		f"can edit the submission."
	)

	print(f"Sending edit link for {item.id} to {emails}")
	send_mail(
		f"[HSSI] '{software.softwareName}' Submission Confirmed!", 
		message, 
		None, 
		emails
	)
	
	return True

def email_edit_link(submission: SubmissionInfo):
	"""
	creates a new edit queue item in the database and emails an edit link
	based on it to the submitter's email
	"""
	software: Software = submission.software
	user: Person = submission.submitter.person
	queue_item = SoftwareEditQueue.create(software)
	link = f"https://hssi.hsdcloud.org/curate/edit_submission/?uid={str(queue_item.id)}"
	message = (
		f"Hello {user.firstName}, \n\n" +
		f"We have received a request to email you a new edit link. You can use " +
		f"the link below to edit your submission: \n\n{link}\n\n" +
		f"Note that this link will expire in 5 hours " +
		f"(UTC {str(queue_item.expiration)})."
	)

	emails = submission.submitter.email_list()
	print(f"Creating and sending edit link for {queue_item.id} to {emails}...")
	send_mail(
		f"[HSSI] Link to edit '{software.softwareName}' submission", 
		message, 
		None, 
		emails
	)