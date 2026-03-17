"""API views for Software JSON responses and optional relation expansion."""

from typing import Any

from django.db.models import Model
from django.db import transaction
from rest_framework import status
from rest_framework.request import HttpRequest
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.parsers import JSONParser
from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import serializers
from rest_framework.generics import GenericAPIView

from ...models import Software, VerifiedSoftware
from ...models.serializers import MODEL_SERIALIZER_MAP
from ...models.serializers.software import SoftwareSerializer
from ...models.serializers.submission import SubmissionSerializer
from ...models.serializers.util import SerialView


def serialize_related(obj: Model) -> str | dict[str, Any]:
	"""Serialize a related object using its serializer or fall back to str()."""
	
	serializer_cls = MODEL_SERIALIZER_MAP.get(obj.__class__)
	if serializer_cls:
		return serializer_cls(obj).data
	return str(obj)

def serialize_with_relations(obj: Model) -> dict[str, Any]:
	"""Serialize a model instance with FK/M2M expanded via serializers or str()."""

	data: dict[str, Any] = {}
	for field in obj._meta.get_fields():
		if field.auto_created:
			continue
		if field.many_to_many and not field.concrete:
			continue
		if field.many_to_many:
			related = getattr(obj, field.name).all()
			data[field.name] = [serialize_related(item) for item in related]
			continue
		if field.many_to_one:
			related = getattr(obj, field.name)
			data[field.name] = serialize_related(related) if related else None
			continue
		data[field.name] = getattr(obj, field.name)
	return data

class SoftwareDetailAPI(GenericAPIView):
	"""Return a single visible Software record, with optional flat expansion."""

	serializer_class = SoftwareSerializer

	def get(self, request: HttpRequest, uid: str) -> Response:
		visible_ids = VerifiedSoftware.objects.values_list("id", flat=True)
		software = Software.objects.filter(pk=uid, pk__in=visible_ids).first()
		if software is None:
			return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
		view = request.GET.get("view", "").lower()
		flat = request.GET.get("flat", "false").lower() == "true" and view != "jsonld"
		if flat:
			return Response(serialize_with_relations(software))
		serializer: SoftwareSerializer = self.get_serializer(software)
		return Response(serializer.data)

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
		except serializers.ValidationError as exc:
			return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

		return Response(
			{"status": "ok", "count": len(results), "results": results},
			status=status.HTTP_201_CREATED,
		)
