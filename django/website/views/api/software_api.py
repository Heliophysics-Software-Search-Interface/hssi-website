"""API views for Software JSON responses and optional relation expansion."""

from typing import Any

from django.db.models import Model
from rest_framework.request import Request
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from ...models import Software, VerifiedSoftware
from ...models.serializers import MODEL_SERIALIZER_MAP
from ...models.serializers.software import SoftwareSerializer


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

@api_view(["GET"])
def software_detail_api(request: Request, uid: str) -> Response:
	"""Return a single visible Software record, with optional flat expansion."""
	visible_ids = VerifiedSoftware.objects.values_list('id', flat=True)
	software = Software.objects.filter(pk=uid, pk__in=visible_ids).first()
	if software is None:
		return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
	flat = request.GET.get("flat", "false").lower() == "true"
	if flat:
		return Response(serialize_with_relations(software))
	return Response(SoftwareSerializer(software).data)

@api_view(["GET"])
def software_list_api(request: Request) -> Response:
	"""Return a list of visible Software IDs with their names."""
	visible_ids = VerifiedSoftware.objects.values_list('id', flat=True)
	entries = (
		Software.objects
		.filter(pk__in=visible_ids)
		.values("id", "software_name")
		.order_by("software_name")
	)
	data = [{"id": str(item["id"]), "name": item["software_name"]} for item in entries]
	return Response({"data": data})
