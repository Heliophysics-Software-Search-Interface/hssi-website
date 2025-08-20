import ast, json

from django.apps import apps
from django.http import JsonResponse, HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from ..forms import *
from ..models import (
	HssiModel, Keyword, OperatingSystem, Phenomena, RepoStatus, Image,
	ProgrammingLanguage, DataInput, CpuArchitecture,  FileFormat, Region,
	InstrumentObservatory, FunctionCategory, License, Organization,
	Person, Curator, Submitter, Award, RelatedItem,
	SubmissionInfo, SoftwareVersion, Software,
)
from ..models.structurizer import ModelStructure, register_structure

register_structure(*[
		ModelStructure.create(Keyword),
		ModelStructure.create(OperatingSystem),
		ModelStructure.create(Phenomena),
		ModelStructure.create(RepoStatus),
		ModelStructure.create(Image),
		ModelStructure.create(ProgrammingLanguage),
		ModelStructure.create(DataInput),
		ModelStructure.create(CpuArchitecture),
		ModelStructure.create(FileFormat),
		ModelStructure.create(Region),
		ModelStructure.create(InstrumentObservatory),
		ModelStructure.create(FunctionCategory),
		ModelStructure.create(License),
		ModelStructure.create(Organization),
		ModelStructure.create(Person),
		# ModelStructure.create(Curator),
		ModelStructure.create(Submitter),
		ModelStructure.create(Award),
		# ModelStructure.create(Functionality),
		ModelStructure.create(RelatedItem),
		# ModelStructure.create(SubmissionInfo),
		ModelStructure.create(SoftwareVersion),
		ModelStructure.create(Software),
		ModelStructure.create(VisibleSoftware),
	])

def get_model_structure(request: HttpRequest) -> JsonResponse:
	structures = { "data": [
		*[x.serialized() for x in registered_structures.values()],
	], "fieldMap": MODEL_FIELD_MAP }
	return JsonResponse(structures)

def get_model_choices(
		request: HttpRequest, 
		model_name: str
	) -> JsonResponse | HttpResponseBadRequest:

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
	return render(
		request, 
		"pages/model_form.html", 
		{ "structure_name": model_name }
	)