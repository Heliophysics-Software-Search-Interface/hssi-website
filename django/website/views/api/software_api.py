"""API views for Software JSON responses and optional relation expansion."""

from typing import Any
import datetime
import uuid

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
from .permissions import HasUpdateToken


class HSSIGenericAPIView(GenericAPIView):
	
	def get_serializer(self, *args, **kwargs) -> serializers.Serializer:
		return super().get_serializer(*args, **kwargs)

@method_decorator(csrf_exempt, name="dispatch")
class SoftwareDetailAPI(HSSIGenericAPIView):
	"""Return or partially update a single visible Software record.

	GET is public and renders via ``SoftwareSerializer``. PATCH is a
	partial metadata update gated by a bearer token; it renders via
	``SubmissionSerializer`` in USER view so the same validation and
	field-mapping used by the create endpoint also governs updates.
	"""

	serializer_class = SoftwareSerializer
	default_view: SerialView = SerialView.STANDARD
	authentication_classes = []

	def get_permissions(self):
		if self.request.method == "PATCH":
			return [HasUpdateToken()]
		return [AllowAny()]

	def get_serializer_class(self):
		if self.request.method == "PATCH":
			return SubmissionSerializer
		return SoftwareSerializer

	def _get_visible_software(self, uid_or_slug: str | uuid.UUID) -> Software | None:
		if not isinstance(uid_or_slug, uuid.UUID):
			return Software.objects.filter(
				pk=VerifiedSoftware.objects.filter(slug=uid_or_slug).first().pk
			).first()
		visible_ids = VerifiedSoftware.objects.values_list("id", flat=True)
		return Software.objects.filter(pk=uid_or_slug, pk__in=visible_ids).first()

	def get(self, request: HttpRequest, uid: str | uuid.UUID) -> Response:
		software = self._get_visible_software(uid)
		if software is None:
			return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
		serializer: SoftwareSerializer = self.get_serializer(software)
		serializer.default_view = self.default_view
		return Response(serializer.data)

	def patch(self, request: HttpRequest, uid: str | uuid.UUID) -> Response:
		software = self._get_visible_software(uid)
		if software is None:
			return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

		serializer = self.get_serializer(
			software,
			data=request.data,
			partial=True,
		)
		serializer._view = SerialView.USER
		serializer.is_valid(raise_exception=True)
		updated = serializer.save()

		return Response({
			"status": "ok",
			"softwareId": str(updated.id),
			"fieldsUpdated": sorted(serializer.validated_data.keys()),
		})

class SoftwareViewAPI(SoftwareDetailAPI):
	default_view: SerialView = SerialView.USER

class SoftwareListAPI(APIView):
	"""Return a list of visible Software IDs with their names.

	Supports an optional ``?repo_url=`` query parameter for exact-match
	lookup by ``code_repository_url``. This is the lookup path used by
	the updater to resolve a repo URL to a software UUID.
	"""

	authentication_classes = []
	permission_classes = [AllowAny]

	def get(self, request: HttpRequest) -> Response:
		visible_ids = VerifiedSoftware.objects.values_list("id", flat=True)
		queryset = Software.objects.filter(pk__in=visible_ids)

		repo_url = request.query_params.get("repo_url")
		if repo_url:
			queryset = queryset.filter(code_repository_url__iexact=repo_url.strip())

		entries = queryset.values("id", "software_name").order_by("software_name")
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
