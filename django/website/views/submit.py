import json, uuid, datetime
from uuid import UUID

from django.shortcuts import render, redirect, HttpResponse
from django.http import (
	HttpRequest, HttpResponseBadRequest, 
	JsonResponse, HttpResponseRedirect, HttpResponseServerError,
)

from ..forms import (
	SUBMISSION_FORM_FIELDS_1,
	SUBMISSION_FORM_FIELDS_2,
	SUBMISSION_FORM_FIELDS_3,
	SUBMISSION_FORM_FIELDS_AGREEMENT,
)
from ..models import *
from ..forms.names import *

def view_form(request: HttpRequest) -> HttpResponse:
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

	return redirect(f"/submit/submitted?id={str(submisison_id)}")

def handle_submission_data(data: dict) -> uuid.UUID:
	software = Software()

	software.persistentIdentifier = data.get(FIELD_PERSISTENTIDENTIFIER)
	software.codeRepositoryUrl = data.get(FIELD_CODEREPOSITORYURL)
	software.softwareName = data.get(FIELD_SOFTWARENAME)
	software.description = data.get(FIELD_DESCRIPTION)
	software.conciseDescription = data.get(FIELD_CONCISEDESCRIPTION)

	## SUBMISSION
	
	submission = SubmissionInfo()

	submitter_data: dict = data.get(FIELD_SUBMITTERNAME)
	submitter_name: str = submitter_data.get(FIELD_SUBMITTERNAME)
	submitter_lastname = submitter_name.split()[-1]
	submitter_firstname = submitter_name.replace(submitter_lastname, '').strip()

	submitter_person = Person()
	submitter_person.lastName = submitter_lastname
	submitter_person.firstName = submitter_firstname
	submitter_person.save()
	
	submission.dateModified = date.today()
	submission.modificationDescription = "Initial submission"
	submission.metadataVersionNumber = "0.1.0"
	submission.submissionDate = date.today()
	submission.internalStatusNote = "Not assigned or reviewed"

	# submission must exist in db before any values can be added to m2m field
	submission.save()
	
	submitter_emails = submitter_data.get(FIELD_SUBMITTEREMAIL)
	for submitter_email in submitter_emails:
		submitter = Submitter()
		submitter.email = submitter_email
		submitter.person = submitter_person
		submitter.save()
		submission.submitter.add(submitter)

	submission.save()
	software.submissionInfo = submission

	## LICENSE

	license_data: dict = data.get(FIELD_LICENSE)
	if license_data:
		license_name = license_data.get(FIELD_LICENSE)
		try:
			uid = UUID(license_name)
			license = License.objects.get(pk=uid)
			software.license = license
		except Exception:
			license = License.objects.filter(name=license_name).first()
			if not license:
				license_url = license_data.get(FIELD_LICENSEURI)
				license = License.objects.filter(url=license_url).first()
			if license: software.license = license

	## DEV STATUS

	devstatus = data.get(FIELD_DEVELOPMENTSTATUS)
	try:
		uid = UUID(devstatus)
		devstatus = RepoStatus.objects.get(pk=uid)
		software.developmentStatus = devstatus
	except Exception:
		devstatus = RepoStatus.objects.filter(name=devstatus).first()
		software.developmentStatus = devstatus
	
	## PUBLISHER

	publisher_data: dict = data.get(FIELD_PUBLISHER)
	if publisher_data:
		publisher = Organization()
		publisher.name = publisher_data.get(FIELD_PUBLISHER)
		publisher.identifier = publisher_data.get(FIELD_PUBLISHERIDENTIFIER)
		publisher.save()
		software.publisher = publisher

	## VERSION
	# TODO remove software foreign key field in SoftwareVersion model

	version_data: dict = data.get(FIELD_VERSIONNUMBER)
	if version_data:
		version = SoftwareVersion()
		version.number = version_data.get(FIELD_VERSIONNUMBER)

		version_date = version_data.get(FIELD_VERSIONDATE)
		if version_date:
			version_date = datetime.datetime.strptime(version_date, '%Y-%m-%d').date()
			version.release_date = version_date

		version.description = version_data.get(FIELD_VERSIONDESCRIPTION)
		version.version_pid = version_data.get(FIELD_VERSIONPID)

	# software needs to be inside database table before any values are added to
	# any of its M2M fields or other fields with foreign keys that need to 
	# reference it
	software.save()

	## AUTHORS

	author_datas: list[dict] = data.get(FIELD_AUTHORS)
	for author_data in author_datas:
		author = Person()
		author.identifier = author_data.get(FIELD_AUTHORIDENTIFIER)
		
		author_name: str = author_data.get(FIELD_AUTHORS)
		author_lastname = author_name.split()[-1]
		author_firstname = author_name.replace(author_lastname, '').strip()

		author.lastName = author_lastname
		author.firstName = author_firstname
		author.save()

		affiliation_datas: dict = author_data.get(FIELD_AUTHORAFFILIATION)
		if affiliation_datas:
			for affiliation_data in affiliation_datas:
				affiliation_name = affiliation_data.get(FIELD_AUTHORAFFILIATION)
				affiliation_id = affiliation_data.get(FIELD_AUTHORAFFILIATIONIDENTIFIER)

				affiliation = Organization()
				affiliation.name = affiliation_name
				affiliation.identifier = affiliation_id
				affiliation.save()
				author.affiliation.add(affiliation)

		author.save()
		software.authors.add(author)

	pub_date = data.get(FIELD_PUBLICATIONDATE)
	if pub_date: 
		pub_date = datetime.datetime.strptime(pub_date, '%Y-%m-%d').date()
		software.publicationDate = pub_date

	## PROGRAMMING LANGUAGES
	# TODO make programming language in software model multi

	proglangs = data.get(FIELD_PROGRAMMINGLANGUAGE)
	for lang in proglangs:
		try:
			uid = UUID(lang)
			lang_ref = ProgrammingLanguage.objects.get(pk=uid)
			if lang_ref:
				software.programmingLanguage = lang_ref
				break
		except Exception:
			lang_ref = ProgrammingLanguage.objects.filter(name=lang).first()
			if lang_ref: 
				software.programmingLanguage = lang_ref
				break
	
	software.save()
	return submission.id
