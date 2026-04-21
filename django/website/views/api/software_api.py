"""API views for Software JSON responses and optional relation expansion."""

from typing import Any
import datetime

from django.db import transaction
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.request import HttpRequest
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import serializers
from rest_framework.generics import GenericAPIView

from ...models import Software, VerifiedSoftware, SoftwareEditQueue, SubmissionInfo
from ...models.serializers.software import SoftwareSerializer
from ...models.serializers.submission import SubmissionSerializer
from ...models.serializers.util import SerialView
from ..edit_submission import email_existing_edit_link


class HSSIGenericAPIView(GenericAPIView):
	def get_serializer(self, *args, **kwargs) -> serializers.Serializer:
		return super().get_serializer(*args, **kwargs)

class SoftwareDetailAPI(HSSIGenericAPIView):
	"""Return a single visible Software record, with optional flat expansion."""

	serializer_class = SoftwareSerializer
	default_view: SerialView = SerialView.STANDARD

	def get(self, request: HttpRequest, uid: str) -> Response:
		visible_ids = VerifiedSoftware.objects.values_list("id", flat=True)
		software = Software.objects.filter(pk=uid, pk__in=visible_ids).first()
		if software is None:
			return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
		serializer: SoftwareSerializer = self.get_serializer(software)
		serializer.default_view = self.default_view
		return Response(serializer.data)

class SoftwareViewAPI(SoftwareDetailAPI):
	default_view: SerialView = SerialView.USER

class SoftwareListAPI(APIView):
	"""Return a list of visible Software IDs with their names."""

	authentication_classes = []
	permission_classes = [AllowAny]

	def get(self, request: HttpRequest) -> Response:
		visible_ids = VerifiedSoftware.objects.values_list("id", flat=True)
		entries = (
			Software.objects
			.filter(pk__in=visible_ids)
			.values("id", "software_name")
			.order_by("software_name")
		)
		data = [{"id": str(item["id"]), "name": item["software_name"]} for item in entries]
		return Response({"data": data})

@method_decorator(csrf_exempt, name="dispatch")
class SubmissionAPI(APIView):
	"""Allow submission POST requests with valid JSON data."""

	authentication_classes = []
	permission_classes = [AllowAny]

	def post(self, request: HttpRequest) -> Response:
		if not isinstance(request.data, list):
			return Response(
				{"detail": "Root JSON value must be an array."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		results: list[dict[str, Any]] = []
		submissions: list[Software] = []
		try:
			with transaction.atomic():
				for idx, item in enumerate(request.data):
					serializer = SubmissionSerializer(
						data=item,
						context={"request": request},
					)
					serializer._view = SerialView.USER
					serializer.is_valid(raise_exception=True)
					software = serializer.save()
					results.append({
						"index": idx,
						"softwareId": str(software.id),
					})
					submissions.append(software)
		except serializers.ValidationError as exc:
			return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
		
		for submission in submissions:
			SoftwareEditQueue.create(submission, timezone.now() + datetime.timedelta(days=90))
			submission_info = SubmissionInfo.objects.get(software=submission)
			email_existing_edit_link(submission_info)

		return Response(
			{"status": "ok", "count": len(results), "results": results},
			status=status.HTTP_201_CREATED,
		)
