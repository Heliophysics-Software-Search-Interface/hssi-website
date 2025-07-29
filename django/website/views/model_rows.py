import json, uuid, enum

import django.apps
from django.http import *

from ..util import *
from ..models import *

def get_model_row(request: HttpRequest, model_name: str, uid: str) -> JsonResponse:
	""" 
	serialize and get json response for a django instance with the specified 
	uid of the specified model 
	"""
	app_label = Software._meta.app_label
	model = django.apps.apps.get_model(app_label, model_name)
	if not (model and issubclass(model, HssiModel)):
		return HttpResponseBadRequest(f"Model '{model_name}' is invalid")
	
	# for debugging purposes, get the first uid if invalid uid specified
	id: uuid.UUID = None
	try: id = uuid.UUID(uid)
	except Exception: id = model.objects.first().id

	access = AccessLevel.from_user(request.user)
	obj = model.objects.get(pk=id)
	data = obj.get_serialized_data(access, True)

	return JsonResponse(data)
