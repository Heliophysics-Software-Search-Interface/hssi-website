import json

from django.shortcuts import render, redirect, HttpResponse
from django.http import (
	HttpRequest, HttpResponseBadRequest, 
	JsonResponse, HttpResponseRedirect
)
from ..forms import (
	SUBMISSION_FORM_FIELDS_1,
	SUBMISSION_FORM_FIELDS_2,
	SUBMISSION_FORM_FIELDS_3,
	SUBMISSION_FORM_FIELDS_AGREEMENT,
)

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

	# TODO parse json_data and save to database
	print("recieved form data", json_data)
	submisison_id: str = ""

	return redirect(f"/submit/submitted?id={submisison_id}")
