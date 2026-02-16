import json, uuid, enum

import django.apps
from django.http import *

from ..util import *
from ..models import *
from ..forms.submission_data import *

def get_fields_param(get: QueryDict) -> list[str] | None:
	fields: list[str] | None = None
	fields_param: str = get.get("columns")
	if fields_param:
		fields = fields_param.split(",")
	return fields

def get_recursive_param(get: QueryDict) -> bool:
	return get.get("recursive", "false").lower() == "true"

def get_model_rows_all(request: HttpRequest, model_name: str) -> JsonResponse:
	"""
	serializes (non-recursively) all objects in a specified model into json and 
	responds to the client with the result
	"""
	app_label = Software._meta.app_label
	model = django.apps.apps.get_model(app_label, model_name)
	if not (model and issubclass(model, HssiModel)):
		return HttpResponseBadRequest(f"Model '{model_name}' is invalid")
	
	access = AccessLevel.from_user(request.user)
	if access < model.access:
		raise Exception(f"Unauthorized access, {access} < {model.access}")
		
	objects = model.objects.all()
	arr: list[dict[str, Any]] = []

	fields = get_fields_param(request.GET)
	recurse = get_recursive_param(request.GET)

	for object in objects:
		try:
			objdata = object.get_serialized_data(access, recurse, fields=fields)
			arr.append(objdata)
		except Exception as e:
			print(e)
			continue
	
	return JsonResponse({"data": arr})

def get_model_row(request: HttpRequest, model_name: str, uid: str) -> JsonResponse:
	""" 
	serialize and get json response for a django instance with the specified 
	uid of the specified model 
	"""
	app_label = Software._meta.app_label
	model = django.apps.apps.get_model(app_label, model_name)
	if issubclass(model, SoftwareEditQueue):
		return HttpResponseForbidden()
	if not (model and issubclass(model, HssiModel)):
		return HttpResponseBadRequest(f"Model '{model_name}' is invalid")
	
	# for debugging purposes, get the first uid if invalid uid specified
	id: uuid.UUID = None
	try: id = uuid.UUID(uid)
	except Exception: id = model.objects.first().id

	fields = get_fields_param(request.GET)
	recurse = get_recursive_param(request.GET)
	
	access = AccessLevel.from_user(request.user)
	obj = model.objects.get(pk=id)
	data: dict = None
	try: data = obj.get_serialized_data(access, recurse, fields=fields)
	except Exception: return HttpResponseForbidden("Unauthorized")

	return JsonResponse(data)

def api_view(request: HttpRequest, uid: str) -> JsonResponse:
	""" user-friendly data view of software submission data """
	software: Software = None
	access = AccessLevel.from_user(request.user)
	access_ovr = AccessLevel.PUBLIC
	try: 
		softwareid = uuid.UUID(uid)
		software = VisibleSoftware.objects.get(pk=softwareid)
		access_ovr = VisibleSoftware.target_model.access
	except Exception: 
		try:
			softwareid = uuid.UUID(uid)
			software_edit = SoftwareEditQueue.objects.get(target_software=softwareid)
			software = Software.objects.get(pk=software_edit.target_software.pk)
			access_ovr = Software.access
		except:
			return HttpResponseBadRequest(f"Invalid ID '{uid}'")

	software = Software.objects.get(pk=software.pk)

	data = SUBMISSION_FORM_FIELDS.serialize_model_object(
		software, 
		True, 
		access, 
		access_ovr
	)

	try:
		submitter_data = SUBMISSION_FORM_SUBMITTER.serialize_model_object(
			software.submissionInfo.submitter, 
			False,
			access,
			access_ovr
		)
		submitter_data["id"] = software.submissionInfo.submitter.id
		data[FIELD_SUBMITTERNAME] = submitter_data
	except Exception as e:
		print(e)

	# format controlled lists to only be name strings instead 
	# of database rows
	def format_controlled_list(field_name: str):
		clist = data.get(field_name)
		if clist is None: return
		for i, obj in enumerate(clist):
			name = obj.get("name", None)
			if name: clist[i] = name

	format_controlled_list(FIELD_SOFTWAREFUNCTIONALITY)
	format_controlled_list(FIELD_PROGRAMMINGLANGUAGE)
	format_controlled_list(FIELD_DATASOURCES)
	format_controlled_list(FIELD_INPUTFORMATS)
	format_controlled_list(FIELD_OUTPUTFORMATS)
	format_controlled_list(FIELD_OPERATINGSYSTEM)
	format_controlled_list(FIELD_CPUARCHITECTURE)
	format_controlled_list(FIELD_RELATEDPHENOMENA)

	return JsonResponse(data)