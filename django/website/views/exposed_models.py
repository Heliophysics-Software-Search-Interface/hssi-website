"""
Views that expose the form structures and model choices the frontend form system
needs, plus the generic single-model form page. Touch this when the frontend
needs new form structure data or choice lists.
"""

import ast, json

from django.apps import apps
from django.http import JsonResponse, HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from ..forms import *
from ..models import HssiModel, Software

def get_model_structure(request: HttpRequest) -> JsonResponse:
	"""
	Returns JSON of every registered form structure, serialized, plus the model
	field map.
	"""
	structures = { "data": [
		*[x.serialized() for x in registered_structures.values()],
	], "fieldMap": MODEL_FIELD_MAP }
	return JsonResponse(structures)

def get_model_choices(
		request: HttpRequest, 
		model_name: str
	) -> JsonResponse | HttpResponseBadRequest:
	"""
	Returns JSON of the choices for every object of an `HssiModel`, filtered by
	the GET parameters (evaluated as Python literals); 400 if the model is not
	an `HssiModel`.
	"""

	filter_dict = request.GET.dict()
	for key, val in filter_dict.items():
		filter_dict[key] = ast.literal_eval(val)

	app_label = Software._meta.app_label
	model = apps.get_model(app_label, model_name)
	if issubclass(model, HssiModel):
		if filter_dict:
			objs = model.objects.filter(**filter_dict)
		else:
			objs = model.objects.all()
		data = {
			"data": [
				obj.get_choice()
				for obj in objs
			]
		}
		return JsonResponse(data)
		
	return HttpResponseBadRequest(
		f"Target model must inherit from {HssiModel.__name__}"
	)

def model_form(request: HttpRequest, model_name: str) -> HttpResponse:
	"""Renders the model form page for the named form structure."""
	return render(
		request, 
		"pages/model_form.html", 
		{ "structure_name": model_name }
	)