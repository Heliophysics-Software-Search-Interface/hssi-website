import json, uuid, enum

from django.core.mail import send_mail
from django.http import *
from django.shortcuts import render
from datetime import timedelta

from ..data_parser import handle_submission_data
from ..util import *
from ..models import *
from ..models.serializers.util import get_registered_serializer, serialize_obj_userfriendly

from ..forms import (
	SUBMISSION_FORM_FIELDS_1,
	SUBMISSION_FORM_FIELDS_2,
	SUBMISSION_FORM_FIELDS_3
)

def _mask_email(email: str) -> str:
	"""Masks all but the first and last characters of the local part of an email."""
	at_pos = email.find('@')
	if at_pos < 0:
		return email
	local = email[:at_pos]
	domain = email[at_pos:]
	if len(local) <= 1:
		return email
	if len(local) == 2:
		return local[0] + '*' + domain
	return local[0] + ('*' * (len(local) - 2)) + local[-1] + domain

def get_masked_submitter_emails(request: HttpRequest, uid: str) -> HttpResponse:
	"""Returns masked submitter email(s) for a software so the user can verify which email to enter."""
	if request.method != "GET": return HttpResponseBadRequest("expected GET")
	try:
		software = Software.objects.get(pk=uuid.UUID(uid))
		submission_info = SubmissionInfo.objects.filter(software=software).first()
		if not submission_info:
			return JsonResponse({"emails": []})
		all_emails: list[str] = []
		for submitter in submission_info.submitter.all():
			all_emails += submitter.email_list()
		masked = [_mask_email(e) for e in all_emails]
		return JsonResponse({"emails": masked})
	except Exception:
		return HttpResponseServerError()

def request_edit_link(request: HttpRequest, uid: str) -> HttpResponse:
	""" http view for requesting an edit link to a given software uid """
	if request.method != "POST": return HttpResponseBadRequest("expected POST")
	try:
		test_email = request.body.decode("utf-8").lower()
		if len(test_email) <= 0: return HttpResponseBadRequest()
		id = uuid.UUID(uid)
		software = Software.objects.get(pk=id)
		for si in software.submission_info.all():
			for submitter in si.submitter.all():
				for correct_email in submitter.email_list():
					if test_email == correct_email.lower():
						email_edit_link(si)
						return HttpResponse(status=204)
		return HttpResponseBadRequest("Incorrect email")

	except Exception:
		import traceback; traceback.print_exc()
		return HttpResponseServerError()

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
	submission_info = SubmissionInfo.objects.filter(software=queue_item.target_software).first()
	submitter_data = serialize_obj_userfriendly(submission_info.submitter.first())
	data["submissionInfo"] = {
		"submitter": submitter_data
	}

	return JsonResponse(data)

def edit_submission(request: HttpRequest) -> HttpResponse:
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

	except Exception as e: 
		print(e)
		return HttpResponseServerError()
	return HttpResponse(status=204)

def email_existing_edit_link(submission: SubmissionInfo) -> bool:
	"""
	grabs an edit link from the software edit queue whose expiration date is 
	the furthest away and emails that to the submitter in the submission info,
	returns false if no edit link exists
	"""
	item = SoftwareEditQueue.get_latest_expiry(submission.software)
	if not item or item.is_expired(): return False
	
	submitter: Submitter = submission.submitter.first()
	emails: list[str] = []
	for submitter in submission.submitter.all():
		emails += submitter.email_list()
	user: Person = submitter.person
	software: Software = submission.software
	link = f"https://hssi.hsdcloud.org/curate/edit_submission/?uid={str(item.id)}"

	message = (
		f"Hello {user.given_name}, \n\n" +
		f"Thank you for submitting your software to HSSI. Once your submission " +
		f"is reviewed, a curator will contact you at this email.\n" +
		f"In the meantime, you can view or edit your submission with the " +
		f"link below: \n\n{link}\n\n" +
		f"Please do not share this link publicly, as anyone with this link " +
		f"can edit the submission." +
		f"Note that this link will expire on " +
		f"UTC {item.expiration.strftime("%Y-%m-%d %H:%M")}."
	)

	print(f"Sending edit link for {item.id} to {emails}")
	send_mail(
		f"[HSSI] '{software.software_name}' Submission Confirmed!", 
		message, 
		None, 
		emails
	)
	
	return True

def email_edit_link(submission: SubmissionInfo, expire_time: timedelta = timedelta(days=90)):
	"""
	creates a new edit queue item in the database and emails an edit link
	based on it to the submitter's email
	"""
	software: Software = submission.software
	first_submitter: Submitter = submission.submitter.first()
	user: Person = first_submitter.person
	expiration: datetime.datetime = datetime.datetime.now() + expire_time
	queue_item = SoftwareEditQueue.create(software, expiration)
	link = f"https://hssi.hsdcloud.org/curate/edit_submission/?uid={str(queue_item.id)}"
	message = (
		f"Hello {user.given_name}, \n\n" +
		f"We have received a request to email you a new edit link. "+
		f"You can use " +
		f"the link below to edit your submission " +
		f"'{software.software_name}': \n\n{link}\n\n" +
		f"Note that this link will expire on " +
		f"UTC {queue_item.expiration.strftime("%Y-%m-%d %H:%M")}."
	)

	emails = []
	for submitter in submission.submitter.all():
		emails += submitter.email_list()
	print(f"Creating and sending edit link for {queue_item.id} to {emails}...")
	send_mail(
		f"[HSSI] Link to edit '{software.software_name}' submission", 
		message, 
		None, 
		emails
	)