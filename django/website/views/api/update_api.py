"""Isolated endpoints and helpers for authenticated Software metadata updates."""

from __future__ import annotations

import secrets
import uuid
from typing import Any
from urllib.parse import urlparse, urlunparse

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.db.models import QuerySet
from django.utils.dateparse import parse_date
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import serializers, status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from hssi.camel_case_renderer import decamelize_data

from ...models import (
	Award,
	ControlledGraphList,
	ControlledList,
	CpuArchitecture,
	DataInput,
	FileFormat,
	FunctionCategory,
	InstrObsType,
	InstrumentObservatory,
	Keyword,
	License,
	OperatingSystem,
	Organization,
	Person,
	Phenomena,
	ProgrammingLanguage,
	Region,
	RelatedItem,
	RelatedItemType,
	RepoStatus,
	Software,
	SoftwareVersion,
	VerifiedSoftware,
)


USER_ALLOWED_FIELDS: frozenset[str] = frozenset({
	"submitter",
	"software_name",
	"code_repository_url",
	"description",
	"concise_description",
	"documentation",
	"persistent_identifier",
	"publication_date",
	"logo",
	"publisher",
	"license",
	"development_status",
	"reference_publication",
	"authors",
	"programming_language",
	"input_formats",
	"output_formats",
	"operating_system",
	"cpu_architecture",
	"software_functionality",
	"related_region",
	"related_phenomena",
	"data_sources",
	"keywords",
	"related_instruments",
	"related_observatories",
	"related_publications",
	"related_datasets",
	"related_software",
	"interoperable_software",
	"funder",
	"award",
	"version",
})

USER_LIST_FIELDS: tuple[str, ...] = (
	"authors",
	"programming_language",
	"input_formats",
	"output_formats",
	"operating_system",
	"cpu_architecture",
	"software_functionality",
	"related_region",
	"related_phenomena",
	"data_sources",
	"keywords",
	"related_instruments",
	"related_observatories",
	"related_publications",
	"related_datasets",
	"related_software",
	"interoperable_software",
	"funder",
	"award",
)


class HasUpdateToken(BasePermission):
	"""Bearer-token permission for HSSI update endpoints."""

	message = "Missing or invalid update token."

	def has_permission(self, request, view):
		expected = getattr(settings, "HSSI_UPDATE_TOKEN", None)
		if not expected:
			return False
		auth_header = request.META.get("HTTP_AUTHORIZATION", "")
		prefix = "Bearer "
		if not auth_header.startswith(prefix):
			return False
		provided = auth_header[len(prefix):]
		return secrets.compare_digest(provided, expected)


@method_decorator(csrf_exempt, name="dispatch")
class SoftwareUpdateAPI(APIView):
	"""Apply a token-authenticated partial update to a visible Software row."""

	authentication_classes = []
	permission_classes = [HasUpdateToken]

	def post(self, request) -> Response:
		if not isinstance(request.data, dict):
			return Response(
				{"detail": "Root JSON value must be an object."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		software_id = request.data.get("softwareId")
		if not software_id:
			return Response(
				{"softwareId": "This field is required."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		try:
			uuid.UUID(str(software_id))
		except (TypeError, ValueError, AttributeError):
			return Response(
				{"softwareId": "Must be a valid UUID."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		software = get_visible_software(str(software_id))
		if software is None:
			return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

		fields = request.data.get("fields")
		if not isinstance(fields, dict):
			return Response(
				{"fields": "Expected an object."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		try:
			changed = update_software_from_payload(software, fields)
		except serializers.ValidationError as exc:
			return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)

		return Response({
			"status": "ok",
			"softwareId": str(software.id),
			"fieldsUpdated": changed,
		})


@method_decorator(csrf_exempt, name="dispatch")
class SoftwareUpdateLookupAPI(APIView):
	"""Find visible Software update targets by repository URL."""

	authentication_classes = []
	permission_classes = [HasUpdateToken]

	def get(self, request) -> Response:
		code_repository_url = request.query_params.get("code_repository_url")
		if code_repository_url is None or not code_repository_url.strip():
			return Response(
				{"codeRepositoryUrl": "This query parameter is required."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		matches = filter_by_code_repository_url(
			visible_software_queryset(),
			code_repository_url,
		).values(
			"id",
			"software_name",
			"code_repository_url",
		).order_by("software_name")

		data = [{
			"softwareId": str(item["id"]),
			"softwareName": item["software_name"],
			"codeRepositoryUrl": item["code_repository_url"],
		} for item in matches]
		return Response({"data": data})


def visible_software_queryset() -> QuerySet[Software]:
	"""Return visible Software rows only."""
	visible_ids = VerifiedSoftware.objects.values_list("id", flat=True)
	return Software.objects.filter(pk__in=visible_ids)


def get_visible_software(uid: str) -> Software | None:
	"""Look up a Software row only if it is visible."""
	return visible_software_queryset().filter(pk=uid).first()


def filter_by_code_repository_url(
	queryset: QuerySet[Software],
	code_repository_url: str,
) -> QuerySet[Software]:
	"""Filter visible Software by repository URL with lightweight normalization."""
	url = code_repository_url.strip()
	if not url:
		return queryset.none()

	exact_matches = queryset.filter(code_repository_url__iexact=url)
	if exact_matches.exists():
		return exact_matches

	target = canonical_code_repository_url(url)
	if target is None:
		return queryset.none()

	match_ids = []
	for software in queryset.exclude(
		code_repository_url__isnull=True,
	).exclude(
		code_repository_url="",
	).only("id", "code_repository_url"):
		candidate = canonical_code_repository_url(software.code_repository_url)
		if candidate is not None and candidate.casefold() == target.casefold():
			match_ids.append(software.id)

	return queryset.filter(id__in=match_ids)


def canonical_code_repository_url(url: str | None) -> str | None:
	"""Normalize URL variants enough for target discovery, not storage."""
	if url is None:
		return None
	raw = url.strip()
	if not raw:
		return None

	parsed = urlparse(raw)
	if not parsed.netloc:
		return raw.rstrip("/").removesuffix(".git")

	scheme = parsed.scheme.lower()
	netloc = parsed.netloc.lower()
	path_parts = [part for part in parsed.path.split("/") if part]

	if netloc == "github.com" and len(path_parts) >= 2:
		path_parts = path_parts[:2]
	elif netloc == "gitlab.com" and "/-/" in parsed.path:
		dash_index = path_parts.index("-")
		path_parts = path_parts[:dash_index]

	if path_parts:
		path_parts[-1] = path_parts[-1].removesuffix(".git")

	path = "/" + "/".join(path_parts) if path_parts else ""
	return urlunparse((scheme, netloc, path.rstrip("/"), "", "", ""))


def update_software_from_payload(
	software: Software,
	payload: dict[str, Any],
) -> list[str]:
	"""Validate and apply a partial user-view payload to a Software row."""
	data = decamelize_data(payload)
	if not isinstance(data, dict):
		raise serializers.ValidationError({"detail": "Root JSON value must be an object."})
	if not data:
		raise serializers.ValidationError({"detail": "At least one field is required."})

	validate_update_data(data)

	with transaction.atomic():
		changed = apply_user_update_fields(software, data)
		touch_submission_info(software, changed)
	return sorted(changed)


def validate_update_data(data: dict[str, Any]) -> None:
	"""Validate field names and top-level shapes before applying updates."""
	unknown = set(data.keys()) - USER_ALLOWED_FIELDS
	if unknown:
		raise serializers.ValidationError({
			key: "Unknown field." for key in sorted(unknown)
		})

	if "submitter" in data:
		raise serializers.ValidationError({
			"submitter": "Updating submitter is not supported via the update API."
		})

	for field in USER_LIST_FIELDS:
		if field in data and data[field] is not None and not isinstance(data[field], list):
			raise serializers.ValidationError({field: "Expected an array."})

	if "publisher" in data and data["publisher"] is not None and not isinstance(data["publisher"], dict):
		raise serializers.ValidationError({"publisher": "Expected an object."})
	if "version" in data and data["version"] is not None and not isinstance(data["version"], dict):
		raise serializers.ValidationError({"version": "Expected an object."})


def apply_user_update_fields(software: Software, data: dict[str, Any]) -> list[str]:
	"""Apply only fields present in the update payload."""
	changed: list[str] = []

	if "software_name" in data:
		software.software_name = _normalize_term(data["software_name"], "software_name")
		changed.append("software_name")
	if "code_repository_url" in data:
		software.code_repository_url = _validate_optional_url(
			data["code_repository_url"], "code_repository_url"
		)
		changed.append("code_repository_url")
	if "description" in data:
		software.description = _optional_string(data["description"], "description")
		changed.append("description")
	if "concise_description" in data:
		concise = _optional_string(data["concise_description"], "concise_description")
		if concise is not None and len(concise) > 200:
			raise serializers.ValidationError({
				"concise_description": "Must be 200 characters or fewer."
			})
		software.concise_description = concise
		changed.append("concise_description")
	if "documentation" in data:
		software.documentation = _validate_optional_url(data["documentation"], "documentation")
		changed.append("documentation")
	if "persistent_identifier" in data:
		software.persistent_identifier = _validate_optional_url(
			data["persistent_identifier"], "persistent_identifier"
		)
		changed.append("persistent_identifier")
	if "publication_date" in data:
		software.publication_date = _validate_optional_date(
			data["publication_date"], "publication_date"
		)
		changed.append("publication_date")
	if "logo" in data:
		software.logo = _validate_optional_url(data["logo"], "logo")
		changed.append("logo")

	if "publisher" in data:
		software.publisher = None if data["publisher"] is None else _get_or_create_org(data["publisher"])
		changed.append("publisher")
	if "license" in data:
		software.license = _get_license(data["license"])
		changed.append("license")
	if "development_status" in data:
		value = data["development_status"]
		software.development_status = (
			None if value in (None, "") else _get_controlled_item(RepoStatus, value)
		)
		changed.append("development_status")
	if "reference_publication" in data:
		value = data["reference_publication"]
		software.reference_publication = (
			None if value in (None, "") else _get_or_create_related(value, RelatedItemType.PUBLICATION)
		)
		changed.append("reference_publication")

	software.save()

	_set_people(software, data, changed)
	_set_controlled_lists(software, data, changed)
	_set_related_objects(software, data, changed)
	_set_version(software, data, changed)

	software.save()
	return changed


def touch_submission_info(software: Software, changed: list[str]) -> None:
	"""Record the partial update on the most recent SubmissionInfo."""
	submission_info = software.submission_info.order_by("-date_modified").first()
	if submission_info is None:
		return
	submission_info.modification_description = (
		f"Partial update via API: {', '.join(sorted(changed))}"
	)
	submission_info.save()


def _set_people(software: Software, data: dict[str, Any], changed: list[str]) -> None:
	if "authors" not in data:
		return
	authors_data = data["authors"] or []
	authors = [_get_or_create_person(item) for item in authors_data]
	for author, author_data in zip(authors, authors_data, strict=False):
		affiliations = author_data.get("affiliation") or []
		if not isinstance(affiliations, list):
			raise serializers.ValidationError({"affiliation": "Expected an array."})
		for org_data in affiliations:
			if not isinstance(org_data, dict):
				raise serializers.ValidationError({"affiliation": "Expected an object."})
			author.affiliation.add(_get_or_create_org(org_data))
	software.authors.set(authors)
	changed.append("authors")


def _set_controlled_lists(
	software: Software,
	data: dict[str, Any],
	changed: list[str],
) -> None:
	controlled_m2m = {
		"programming_language": (ProgrammingLanguage, software.programming_language),
		"input_formats": (FileFormat, software.input_formats),
		"output_formats": (FileFormat, software.output_formats),
		"operating_system": (OperatingSystem, software.operating_system),
		"cpu_architecture": (CpuArchitecture, software.cpu_architecture),
		"data_sources": (DataInput, software.data_sources),
	}
	for field, (model, manager) in controlled_m2m.items():
		if field in data:
			manager.set([
				_get_controlled_item(model, value)
				for value in (data[field] or [])
			])
			changed.append(field)

	graph_m2m = {
		"software_functionality": (FunctionCategory, software.software_functionality),
		"related_region": (Region, software.related_region),
		"related_phenomena": (Phenomena, software.related_phenomena),
	}
	for field, (model, manager) in graph_m2m.items():
		if field in data:
			manager.set([
				_get_graph_list_item(model, value)
				for value in (data[field] or [])
			])
			changed.append(field)

	if "keywords" in data:
		software.keywords.set([
			_get_or_create_keyword(value)
			for value in (data["keywords"] or [])
		])
		changed.append("keywords")


def _set_related_objects(
	software: Software,
	data: dict[str, Any],
	changed: list[str],
) -> None:
	if "related_instruments" in data:
		software.related_instruments.set([
			_get_or_create_observatory(item, InstrObsType.INSTRUMENT)
			for item in (data["related_instruments"] or [])
		])
		changed.append("related_instruments")
	if "related_observatories" in data:
		software.related_observatories.set([
			_get_or_create_observatory(item, InstrObsType.OBSERVATORY)
			for item in (data["related_observatories"] or [])
		])
		changed.append("related_observatories")

	related_m2m = {
		"related_publications": (software.related_publications, RelatedItemType.PUBLICATION),
		"related_datasets": (software.related_datasets, RelatedItemType.DATASET),
		"related_software": (software.related_software, RelatedItemType.SOFTWARE),
		"interoperable_software": (software.interoperable_software, RelatedItemType.SOFTWARE),
	}
	for field, (manager, item_type) in related_m2m.items():
		if field in data:
			manager.set([
				_get_or_create_related(value, item_type)
				for value in (data[field] or [])
			])
			changed.append(field)

	if "funder" in data:
		software.funder.set([
			_get_or_create_org(item)
			for item in (data["funder"] or [])
		])
		changed.append("funder")
	if "award" in data:
		software.award.set([
			_get_or_create_award(item)
			for item in (data["award"] or [])
		])
		changed.append("award")


def _set_version(
	software: Software,
	data: dict[str, Any],
	changed: list[str],
) -> None:
	if "version" not in data:
		return
	version = data["version"]
	if version is None:
		software.version.clear()
	else:
		version_obj = SoftwareVersion.objects.create(
			number=_normalize_term(version.get("number"), "version.number"),
			release_date=_validate_optional_date(version.get("release_date"), "version.release_date"),
			description=_optional_string(version.get("description"), "version.description"),
			version_pid=_validate_optional_url(version.get("version_pid"), "version.version_pid"),
		)
		software.version.set([version_obj])
	changed.append("version")


def _optional_string(value: Any, field_name: str) -> str | None:
	if value is None:
		return None
	if not isinstance(value, str):
		raise serializers.ValidationError({field_name: "Expected a string."})
	stripped = value.strip()
	return stripped or None


def _normalize_term(value: Any, field_name: str) -> str:
	value = _optional_string(value, field_name)
	if value is None:
		raise serializers.ValidationError({field_name: "Value cannot be empty."})
	return value


def _validate_optional_url(value: Any, field_name: str) -> str | None:
	value = _optional_string(value, field_name)
	if value is None:
		return None
	validator = URLValidator()
	try:
		validator(value)
	except DjangoValidationError:
		raise serializers.ValidationError({field_name: f"Invalid URL: '{value}'"})
	return value


def _validate_optional_date(value: Any, field_name: str):
	value = _optional_string(value, field_name)
	if value is None:
		return None
	parsed = parse_date(value)
	if parsed is None:
		raise serializers.ValidationError({field_name: f"Invalid date: '{value}'"})
	return parsed


def _get_controlled_item(
	model: type[ControlledList],
	value: Any,
) -> ControlledList:
	normalized = _normalize_term(value, model.__name__)
	obj = model.objects.filter(name__iexact=normalized).first()
	if not obj:
		raise serializers.ValidationError({model.__name__: f"Unknown value '{value}'."})
	return obj


def _get_graph_list_item(
	model: type[ControlledGraphList],
	value: Any,
) -> ControlledGraphList:
	normalized = _normalize_term(value, model.__name__)
	if ":" not in normalized:
		obj = model.objects.filter(name__iexact=normalized).first()
		if not obj:
			raise serializers.ValidationError({model.__name__: f"Unknown value '{value}'."})
		return obj

	parts = [part.strip() for part in normalized.split(":")]
	parent = model.objects.filter(name__iexact=parts[0], parent_nodes__isnull=True).first()
	if not parent:
		raise serializers.ValidationError({model.__name__: f"Unknown value '{value}'."})
	for part in parts[1:]:
		child = model.objects.filter(name__iexact=part, parent_nodes=parent).first()
		if not child:
			raise serializers.ValidationError({model.__name__: f"Unknown value '{value}'."})
		parent = child
	return parent


def _get_or_create_keyword(value: Any) -> Keyword:
	normalized = _normalize_term(value, Keyword.__name__)
	obj = Keyword.objects.filter(name__iexact=normalized).first()
	if obj:
		return obj
	return Keyword.objects.create(name=normalized)


def _get_or_create_person(data: Any) -> Person:
	if not isinstance(data, dict):
		raise serializers.ValidationError({"person": "Expected an object."})
	given_name = _normalize_term(data.get("given_name"), "given_name")
	family_name = _normalize_term(data.get("family_name"), "family_name")
	identifier = _validate_optional_url(data.get("identifier"), "identifier")
	if identifier:
		person = Person.objects.filter(identifier=identifier).first()
		if person:
			if not person.given_name:
				person.given_name = given_name
			if not person.family_name:
				person.family_name = family_name
			person.save()
			return person
		return Person.objects.create(
			given_name=given_name,
			family_name=family_name,
			identifier=identifier,
		)

	person = Person.objects.filter(
		given_name=given_name,
		family_name=family_name,
	).first()
	if person:
		return person
	return Person.objects.create(given_name=given_name, family_name=family_name)


def _get_or_create_org(data: Any) -> Organization:
	if not isinstance(data, dict):
		raise serializers.ValidationError({"organization": "Expected an object."})
	name = _normalize_term(data.get("name"), "name")
	identifier = _validate_optional_url(data.get("identifier"), "identifier")
	if identifier:
		org = Organization.objects.filter(identifier=identifier).first()
		if org:
			if not org.name:
				org.name = name
				org.save()
			return org
		return Organization.objects.create(name=name, identifier=identifier)

	org = Organization.objects.filter(name__iexact=name).first()
	if org:
		return org
	return Organization.objects.create(name=name)


def _get_or_create_observatory(
	data: Any,
	instr_type: InstrObsType,
) -> InstrumentObservatory:
	if not isinstance(data, dict):
		raise serializers.ValidationError({"instrument_observatory": "Expected an object."})
	name = _normalize_term(data.get("name"), "name")
	identifier = _validate_optional_url(data.get("identifier"), "identifier")
	if identifier:
		entry = InstrumentObservatory.objects.filter(identifier=identifier).first()
		if entry:
			return entry
		return InstrumentObservatory.objects.create(
			name=name,
			identifier=identifier,
			type=instr_type,
		)
	entry = InstrumentObservatory.objects.filter(name__iexact=name, type=instr_type).first()
	if entry:
		return entry
	return InstrumentObservatory.objects.create(name=name, type=instr_type)


def _get_or_create_award(data: Any) -> Award:
	if not isinstance(data, dict):
		raise serializers.ValidationError({"award": "Expected an object."})
	name = _normalize_term(data.get("name"), "name")
	identifier = _optional_string(data.get("identifier"), "identifier")
	if identifier:
		award = Award.objects.filter(identifier=identifier).first()
		if award:
			return award
		return Award.objects.create(name=name, identifier=identifier)
	award = Award.objects.filter(name__iexact=name).first()
	if award:
		return award
	return Award.objects.create(name=name)


def _get_or_create_related(value: Any, item_type: RelatedItemType) -> RelatedItem:
	identifier = _validate_optional_url(value, "identifier")
	if identifier is None:
		raise serializers.ValidationError({"identifier": "Value cannot be empty."})
	item = RelatedItem.objects.filter(identifier=identifier).first()
	if item:
		return item
	return RelatedItem.objects.create(
		name=identifier,
		identifier=identifier,
		type=item_type,
	)


def _get_license(value: Any) -> License | None:
	if value in (None, ""):
		return None
	normalized = _normalize_term(value, "license")
	license_obj = License.objects.filter(name__iexact=normalized).first()
	if not license_obj:
		raise serializers.ValidationError({"license": f"Unknown license '{value}'."})
	return license_obj
