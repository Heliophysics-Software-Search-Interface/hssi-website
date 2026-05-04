"""Submission API and related logic."""

from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import serializers

from ..base import ControlledList, ControlledGraphList
from ..license import License
from ..organizations import Organization, Award
from ..people import Person, Submitter
from ..related import RelatedItem, RelatedItemType
from ..software import Software, SubmissionInfo, SoftwareVersion
from ..vocab import (
	CpuArchitecture, DataInput, FileFormat, FunctionCategory, InstrObsType,
	InstrumentObservatory, Keyword, OperatingSystem, Phenomena,
	ProgrammingLanguage, Region, RepoStatus,
)
from .util import HssiSerializer


# Every snake-case key accepted by the user-view payload. Keys outside this
# set are rejected with 400 so client typos fail loudly instead of being
# silently dropped.
_USER_ALLOWED_FIELDS: frozenset[str] = frozenset({
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

# Required for a full create. PATCH updates may omit any of these.
_USER_REQUIRED_FIELDS: tuple[str, ...] = (
	"submitter",
	"software_name",
	"code_repository_url",
	"authors",
	"description",
)

# Fields whose payload value, when present, must be a JSON array.
_USER_LIST_FIELDS: tuple[str, ...] = (
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


class SubmissionSerializer(HssiSerializer):
	"""Serializer and parser for submission data."""

	def _strip_string(self, value: Any) -> str | None:
		if value is None:
			return None
		if not isinstance(value, str):
			raise serializers.ValidationError(f"Expected string, got: {str(value)}")
		return value.strip()

	def _validate_url(self, value: str | None) -> str | None:
		if value is None or value == "":
			return None
		validator = URLValidator()
		try:
			validator(value)
		except DjangoValidationError:
			raise serializers.ValidationError(f"Invalid URL: '{value}'")
		return value

	def _validate_date(self, value: str | None):
		if value is None or value == "":
			return None
		if not isinstance(value, str):
			raise serializers.ValidationError(f"Invalid date: {str(value)}")
		parsed = parse_date(value)
		if parsed is None:
			raise serializers.ValidationError(f"Invalid date: '{value}'")
		return parsed

	def _normalize_term(self, value: str, field_name: str) -> str:
		if not isinstance(value, str):
			raise serializers.ValidationError({field_name: "Expected a string."})
		normalized = value.strip()
		if not normalized:
			raise serializers.ValidationError({field_name: "Value cannot be empty."})
		return normalized

	def _get_graph_list_item(
		self, 
		model: type[ControlledGraphList], 
		value: str, 
	) -> ControlledGraphList:
		normalized = self._normalize_term(value, model.__name__)
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

	def _get_controlled_item(
		self, 
		model: type[ControlledList], 
		value: str, 
	) -> ControlledList:
		normalized = self._normalize_term(value, model.__name__)
		obj = model.objects.filter(name__iexact=normalized).first()
		if not obj:
			raise serializers.ValidationError({model.__name__: f"Unknown value '{value}'."})
		return obj

	def _get_or_create_keyword(self, value: str) -> Keyword:
		normalized = self._normalize_term(value, Keyword.__name__)
		obj = Keyword.objects.filter(name__iexact=normalized).first()
		if obj:
			return obj
		return Keyword.objects.create(name=normalized)

	def _get_or_create_person(self, data: dict[str, Any]) -> Person:
		given_name = self._normalize_term(data.get("given_name"), "givenName")
		family_name = self._normalize_term(data.get("family_name"), "familyName")
		identifier = data.get("identifier")
		if identifier:
			identifier = self._validate_url(self._strip_string(identifier))
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
		return Person.objects.create(
			given_name=given_name,
			family_name=family_name,
		)

	def _get_or_create_org(self, data: dict[str, Any]) -> Organization:
		name = self._normalize_term(data.get("name"), "name")
		identifier = data.get("identifier")
		if identifier:
			identifier = self._validate_url(self._strip_string(identifier))
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

	def _get_or_create_submitter(self, data: dict[str, Any]) -> Submitter:
		email = self._normalize_term(data.get("email"), "email")
		person_data = data.get("person")
		if not isinstance(person_data, dict):
			raise serializers.ValidationError({"person": "Expected an object."})
		person = self._get_or_create_person(person_data)
		submitter = Submitter.objects.filter(email__iexact=email).first()
		if submitter:
			return submitter
		return Submitter.objects.create(email=email, person=person)

	def _get_or_create_observatory(
		self, 
		data: dict[str, Any], 
		instr_type: InstrObsType
	) -> InstrumentObservatory:
		name = self._normalize_term(data.get("name"), "name")
		identifier = data.get("identifier")
		if identifier:
			identifier = self._validate_url(self._strip_string(identifier))
			entry = InstrumentObservatory.objects.filter(identifier=identifier).first()
			if entry:
				return entry
			return InstrumentObservatory.objects.create(
				name=name,
				identifier=identifier,
				type=instr_type,
			)
		entry = InstrumentObservatory.objects.filter(name=name, type=instr_type).first()
		if entry:
			return entry
		return InstrumentObservatory.objects.create(name=name, type=instr_type)

	def _get_or_create_award(self, data: dict[str, Any]) -> Award:
		name = self._normalize_term(data.get("name"), "name")
		identifier = data.get("identifier")
		if identifier:
			identifier = self._normalize_term(identifier, "identifier")
			award = Award.objects.filter(identifier=identifier).first()
			if award:
				return award
			return Award.objects.create(name=name, identifier=identifier)
		award = Award.objects.filter(name__iexact=name).first()
		if award:
			return award
		return Award.objects.create(name=name)

	def _get_or_create_related(self, url: str, item_type: RelatedItemType) -> RelatedItem:
		identifier = self._validate_url(self._normalize_term(url, "identifier"))
		item = RelatedItem.objects.filter(identifier=identifier).first()
		if item:
			return item
		return RelatedItem.objects.create(
			name=identifier,
			identifier=identifier,
			type=item_type,
		)

	def to_internal_value_user(self, data: dict[str, Any]):
		if not isinstance(data, dict):
			raise serializers.ValidationError("Expected an object.")

		# Reject unknown keys during PATCH so client typos fail loudly
		# instead of being silently dropped. Create uses the same whitelist
		# indirectly via the required-field and shape checks below.
		if self.partial:
			unknown = set(data.keys()) - _USER_ALLOWED_FIELDS
			if unknown:
				raise serializers.ValidationError({
					key: "Unknown field." for key in sorted(unknown)
				})

		# Required-field enforcement only runs for creates. Partial updates
		# may omit any key; an omitted key means "leave unchanged".
		if not self.partial:
			errors: dict[str, Any] = {}
			for field in _USER_REQUIRED_FIELDS:
				if field not in data or data[field] in (None, "", [], {}):
					errors[field] = "This field is required."
			if errors:
				raise serializers.ValidationError(errors)

		# Shape checks below must be presence-gated so partial updates that
		# omit a key do not trip validation on a None value.
		if "submitter" in data and not isinstance(data["submitter"], list):
			raise serializers.ValidationError({"submitter": "Expected an array."})
		if "authors" in data and not isinstance(data["authors"], list):
			raise serializers.ValidationError({"authors": "Expected an array."})

		for field in _USER_LIST_FIELDS:
			if field in data and data[field] is not None and not isinstance(data[field], list):
				raise serializers.ValidationError({field: "Expected an array."})

		if "publisher" in data and data["publisher"] is not None and not isinstance(data["publisher"], dict):
			raise serializers.ValidationError({"publisher": "Expected an object."})

		if "code_repository_url" in data:
			self._validate_url(self._strip_string(data.get("code_repository_url")))
		if "documentation" in data:
			self._validate_url(self._strip_string(data.get("documentation")))
		if "persistent_identifier" in data:
			self._validate_url(self._strip_string(data.get("persistent_identifier")))
		if "reference_publication" in data and data.get("reference_publication"):
			self._validate_url(self._strip_string(data.get("reference_publication")))
		if "logo" in data:
			self._validate_url(self._strip_string(data.get("logo")))

		if data.get("publication_date"):
			self._validate_date(data.get("publication_date"))

		if "concise_description" in data:
			concise_description = data.get("concise_description")
			if concise_description is not None:
				stripped = self._strip_string(concise_description) or ""
				if len(stripped) > 200:
					raise serializers.ValidationError(
						{"conciseDescription": "Must be 200 characters or fewer."}
					)

		if "version" in data:
			version = data["version"]
			if version is not None:
				if not isinstance(version, dict):
					raise serializers.ValidationError({"version": "Expected an object."})
				self._normalize_term(version.get("number"), "version.number")
				if version.get("release_date"):
					self._validate_date(version.get("release_date"))
				if version.get("version_pid"):
					self._validate_url(self._strip_string(version.get("version_pid")))

		return data

	def _apply_user_fields(self, software: Software, data: dict[str, Any]):
		"""Apply user-view fields to a Software instance (create or update).

		Presence-based: only keys that appear in ``data`` are applied.
		Missing keys leave the existing value untouched. Empty optional
		values clear the target (e.g. ``license: null`` clears the FK;
		``keywords: []`` empties the M2M). Callers are responsible for
		ensuring required fields are present — that check lives in
		``to_internal_value_user`` and only runs for non-partial input.
		"""
		if "software_name" in data:
			software.software_name = self._normalize_term(
				data["software_name"], "softwareName"
			)
		if "code_repository_url" in data:
			software.code_repository_url = self._validate_url(
				self._strip_string(data["code_repository_url"])
			)
		if "description" in data:
			software.description = self._normalize_term(
				data["description"], "description"
			)
		if "concise_description" in data:
			software.concise_description = self._strip_string(
				data["concise_description"]
			)
		if "documentation" in data:
			software.documentation = self._validate_url(
				self._strip_string(data["documentation"])
			)
		if "persistent_identifier" in data:
			software.persistent_identifier = self._validate_url(
				self._strip_string(data["persistent_identifier"])
			)
		if "publication_date" in data:
			software.publication_date = self._validate_date(data["publication_date"])
		if "logo" in data:
			software.logo = self._validate_url(self._strip_string(data["logo"]))

		if "publisher" in data:
			publisher = data["publisher"]
			if publisher is None:
				software.publisher = None
			else:
				software.publisher = self._get_or_create_org(publisher)

		if "license" in data:
			license_name = data["license"]
			if license_name in (None, ""):
				software.license = None
			else:
				normalized = self._normalize_term(license_name, "license")
				license_obj = License.objects.filter(name__iexact=normalized).first()
				if not license_obj:
					raise serializers.ValidationError(
						{"license": f"Unknown license '{license_name}'."}
					)
				software.license = license_obj

		if "development_status" in data:
			status_value = data["development_status"]
			if status_value in (None, ""):
				software.development_status = None
			else:
				software.development_status = self._get_controlled_item(
					RepoStatus, status_value
				)

		if "reference_publication" in data:
			reference = data["reference_publication"]
			if not reference:
				software.reference_publication = None
			else:
				software.reference_publication = self._get_or_create_related(
					reference, RelatedItemType.PUBLICATION
				)

		# Persist scalars and FKs before touching M2M relations — a new
		# Software instance needs a PK before ``.set()`` can run against it.
		software.save()

		if "authors" in data:
			authors_data = data["authors"] or []
			authors = [self._get_or_create_person(item) for item in authors_data]
			for author, author_data in zip(authors, authors_data, strict=False):
				affiliations = author_data.get("affiliation") or []
				if isinstance(affiliations, list):
					for org_data in affiliations:
						if not isinstance(org_data, dict):
							raise serializers.ValidationError(
								{"affiliation": "Expected an object."}
							)
						author.affiliation.add(self._get_or_create_org(org_data))
			software.authors.set(authors)

		if "programming_language" in data:
			items = [
				self._get_controlled_item(ProgrammingLanguage, item)
				for item in (data["programming_language"] or [])
			]
			software.programming_language.set(items)

		if "input_formats" in data:
			items = [
				self._get_controlled_item(FileFormat, item)
				for item in (data["input_formats"] or [])
			]
			software.input_formats.set(items)

		if "output_formats" in data:
			items = [
				self._get_controlled_item(FileFormat, item)
				for item in (data["output_formats"] or [])
			]
			software.output_formats.set(items)

		if "operating_system" in data:
			items = [
				self._get_controlled_item(OperatingSystem, item)
				for item in (data["operating_system"] or [])
			]
			software.operating_system.set(items)

		if "cpu_architecture" in data:
			items = [
				self._get_controlled_item(CpuArchitecture, item)
				for item in (data["cpu_architecture"] or [])
			]
			software.cpu_architecture.set(items)

		if "software_functionality" in data:
			items = [
				self._get_graph_list_item(FunctionCategory, item)
				for item in (data["software_functionality"] or [])
			]
			software.software_functionality.set(items)

		if "related_region" in data:
			items = [
				self._get_graph_list_item(Region, item)
				for item in (data["related_region"] or [])
			]
			software.related_region.set(items)

		if "related_phenomena" in data:
			items = [
				self._get_graph_list_item(Phenomena, item)
				for item in (data["related_phenomena"] or [])
			]
			software.related_phenomena.set(items)

		if "data_sources" in data:
			items = [
				self._get_controlled_item(DataInput, item)
				for item in (data["data_sources"] or [])
			]
			software.data_sources.set(items)

		if "keywords" in data:
			items = [
				self._get_or_create_keyword(item)
				for item in (data["keywords"] or [])
			]
			software.keywords.set(items)

		if "related_instruments" in data:
			items = [
				self._get_or_create_observatory(item, InstrObsType.INSTRUMENT)
				for item in (data["related_instruments"] or [])
			]
			software.related_instruments.set(items)

		if "related_observatories" in data:
			items = [
				self._get_or_create_observatory(item, InstrObsType.OBSERVATORY)
				for item in (data["related_observatories"] or [])
			]
			software.related_observatories.set(items)

		if "related_publications" in data:
			items = [
				self._get_or_create_related(url, RelatedItemType.PUBLICATION)
				for url in (data["related_publications"] or [])
			]
			software.related_publications.set(items)

		if "related_datasets" in data:
			items = [
				self._get_or_create_related(url, RelatedItemType.DATASET)
				for url in (data["related_datasets"] or [])
			]
			software.related_datasets.set(items)

		if "related_software" in data:
			items = [
				self._get_or_create_related(url, RelatedItemType.SOFTWARE)
				for url in (data["related_software"] or [])
			]
			software.related_software.set(items)

		if "interoperable_software" in data:
			items = [
				self._get_or_create_related(url, RelatedItemType.SOFTWARE)
				for url in (data["interoperable_software"] or [])
			]
			software.interoperable_software.set(items)

		if "funder" in data:
			items = [
				self._get_or_create_org(item)
				for item in (data["funder"] or [])
			]
			software.funder.set(items)

		if "award" in data:
			items = [
				self._get_or_create_award(item)
				for item in (data["award"] or [])
			]
			software.award.set(items)

		if "version" in data:
			version = data["version"]
			if version is None:
				software.version.clear()
			else:
				version_obj = SoftwareVersion.objects.create(
					number=self._normalize_term(version.get("number"), "version_number"),
					release_date=self._validate_date(version.get("release_date")),
					description=self._strip_string(version.get("description")),
					version_pid=self._validate_url(
						self._strip_string(version.get("version_pid"))
					),
				)
				software.version.set([version_obj])

	@transaction.atomic
	def create_user(self, validated_data: dict[str, Any]):
		software = Software()
		self._apply_user_fields(software, validated_data)

		# Submitter is write-once and only attached during initial
		# submission. ``update_user`` rejects any attempt to change it.
		submitters = [
			self._get_or_create_submitter(item)
			for item in validated_data.get("submitter", [])
		]
		submission_info = SubmissionInfo.objects.create(
			software=software,
			submission_date=timezone.now(),
		)
		if submitters:
			submission_info.submitter.set(submitters)

		return software

	@transaction.atomic
	def update_user(self, instance: Software, validated_data: dict[str, Any]):
		# Changing the submitter would require SubmissionInfo membership
		# changes that are out of scope for a partial metadata update. We
		# reject it explicitly rather than silently dropping the key.
		if "submitter" in validated_data:
			raise serializers.ValidationError({
				"submitter": "Updating submitter is not supported via PATCH."
			})

		self._apply_user_fields(instance, validated_data)

		# Touch the most-recent SubmissionInfo so ``date_modified`` auto_now
		# fires and the audit trail records what changed.
		submission_info = instance.submission_info.order_by("-date_modified").first()
		if submission_info is not None:
			changed = sorted(validated_data.keys())
			submission_info.modification_description = (
				f"Partial update via API: {', '.join(changed)}"
			)
			submission_info.save()

		return instance

	class Meta(HssiSerializer.Meta):
		model = Software
		fields = "__all__"
