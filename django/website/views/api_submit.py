import json, datetime

from django.db import transaction
from django.utils import timezone
from django.http import (
	HttpRequest, JsonResponse, HttpResponseBadRequest,
)
from django.views.decorators.csrf import csrf_exempt

from ..models import SubmissionInfo, SoftwareEditQueue
from ..data_parser import handle_submission_data, api_submission_to_formdict
from .edit_submission import email_existing_edit_link

@csrf_exempt
def api_submit(request: HttpRequest):
	print(f"submission endoint {request.method}")
	if request.method != "POST":
		return HttpResponseBadRequest("POST expected")
	try:
		encoding = request.encoding or "utf-8"
		data = json.loads(request.body.decode(encoding))
	except Exception as exc:
		return HttpResponseBadRequest(f"Invalid JSON body: {exc}")

	if not isinstance(data, list):
		return HttpResponseBadRequest("Root JSON value must be an array.")

	results: list[dict] = []
	try:
		with transaction.atomic():
			for idx, item in enumerate(data):
				form_data = api_submission_to_formdict(item)
				submission_id = handle_submission_data(form_data)
				software = SubmissionInfo.objects.get(pk=submission_id).software
				SoftwareEditQueue.create(software, timezone.now() + datetime.timedelta(days=90))
				transaction.on_commit(lambda s=software: email_existing_edit_link(s.submissionInfo))
				results.append({
					"index": idx,
					"submissionId": str(submission_id),
					"softwareId": str(software.id),
				})
	except Exception as exc:
		return HttpResponseBadRequest(str(exc))

	return JsonResponse({
		"status": "ok",
		"count": len(results),
		"results": results,
	})
