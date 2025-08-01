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
from ..models.structurizer import ModelStructure

def get_model_structure(request: HttpRequest) -> JsonResponse:
	structures = { "data": [
		ModelStructure.create(Keyword).serialized(),
		ModelStructure.create(OperatingSystem).serialized(),
		ModelStructure.create(Phenomena).serialized(),
		ModelStructure.create(RepoStatus).serialized(),
		ModelStructure.create(Image).serialized(),
		ModelStructure.create(ProgrammingLanguage).serialized(),
		ModelStructure.create(DataInput).serialized(),
		ModelStructure.create(CpuArchitecture).serialized(),
		ModelStructure.create(FileFormat).serialized(),
		ModelStructure.create(Region).serialized(),
		ModelStructure.create(InstrumentObservatory).serialized(),
		ModelStructure.create(FunctionCategory).serialized(),
		ModelStructure.create(License).serialized(),
		ModelStructure.create(Organization).serialized(),
		ModelStructure.create(Person).serialized(),
		# ModelStructure.create(Curator).serialized(),
		ModelStructure.create(Submitter).serialized(),
		ModelStructure.create(Award).serialized(),
		# ModelStructure.create(Functionality).serialized(),
		ModelStructure.create(RelatedItem).serialized(),
		# ModelStructure.create(SubmissionInfo).serialized(),
		ModelStructure.create(SoftwareVersion).serialized(),
		ModelStructure.create(Software).serialized(),
		*[
			SUBMISSION_FORM_OBSERVATORY.serialized(), 
			SUBMISSION_FORM_AUTHOR.serialized(), 
			SUBMISSION_FORM_CONTRIBUTOR.serialized(), 
			SUBMISSION_FORM_AWARD.serialized(), 
			SUBMISSION_FORM_DATASET.serialized(), 
			SUBMISSION_FORM_INSTRUMENT.serialized(),
			SUBMISSION_FORM_LICENSE.serialized(), 
			SUBMISSION_FORM_AUTHOR_AFFILIATION.serialized(), 
			SUBMISSION_FORM_CONTRIBUTOR_AFFILIATION.serialized(),
			SUBMISSION_FORM_PUBLISHER.serialized(), 
			SUBMISSION_FORM_FUNDER.serialized(), 
			SUBMISSION_FORM_PUBLICATION.serialized(), 
			SUBMISSION_FORM_REL_SOFTWARE.serialized(), 
			SUBMISSION_FORM_SUBMITTER.serialized(), 
			SUBMISSION_FORM_VERSION.serialized(),
			SUBMISSION_FORM_FIELDS.serialized(),
			SUBMISSION_FORM_FIELDS_1.serialized(),
			SUBMISSION_FORM_FIELDS_2.serialized(),
			SUBMISSION_FORM_FIELDS_3.serialized(),
		],
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
