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

		required_fields = [
			"submitter",
			"software_name",
			"code_repository_url",
			"authors",
			"description",
		]
		errors: dict[str, Any] = {}
		for field in required_fields:
			if field not in data or data[field] in (None, "", [], {}):
				errors[field] = "This field is required."
		if errors:
			raise serializers.ValidationError(errors)

		if not isinstance(data.get("submitter"), list):
			raise serializers.ValidationError({"submitter": "Expected an array."})
		if not isinstance(data.get("authors"), list):
			raise serializers.ValidationError({"authors": "Expected an array."})

		list_fields = [
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
		]
		for field in list_fields:
			if field in data and data[field] is not None and not isinstance(data[field], list):
				raise serializers.ValidationError({field: "Expected an array."})

		if data.get("publisher") is not None and not isinstance(data.get("publisher"), dict):
			raise serializers.ValidationError({"publisher": "Expected an object."})

		self._validate_url(self._strip_string(data.get("code_repository_url")))
		self._validate_url(self._strip_string(data.get("documentation")))
		self._validate_url(self._strip_string(data.get("persistent_identifier")))
		self._validate_url(self._strip_string(data.get("reference_publication")))
		self._validate_url(self._strip_string(data.get("logo")))

		if data.get("publication_date"):
			self._validate_date(data.get("publication_date"))

		concise_description = data.get("concise_description")
		if concise_description is not None:
			concise_description = self._strip_string(concise_description) or ""
			if len(concise_description) > 200:
				raise serializers.ValidationError(
					{"conciseDescription": "Must be 200 characters or fewer."}
				)

		version = data.get("version")
		if version is not None:
			if not isinstance(version, dict):
				raise serializers.ValidationError({"version": "Expected an object."})
			self._normalize_term(version.get("number"), "version.number")
			if version.get("release_date"):
				self._validate_date(version.get("release_date"))
			if version.get("version_pid"):
				self._validate_url(self._strip_string(version.get("version_pid")))

		return data

	@transaction.atomic
	def create_user(self, validated_data: dict[str, Any]):
		software = Software.objects.create(
			software_name=self._normalize_term(
				validated_data.get("software_name"), 
				"softwareName"
			),
			code_repository_url=self._validate_url(
				self._strip_string(validated_data.get("code_repository_url"))
			),
			description=self._normalize_term(
				validated_data.get("description"), 
				"description"
			),
			concise_description=self._strip_string(
				validated_data.get("concise_description")
			),
			documentation=self._validate_url(
				self._strip_string(validated_data.get("documentation"))
			),
			persistent_identifier=self._validate_url(
				self._strip_string(validated_data.get("persistent_identifier"))
			),
			publication_date=self._validate_date(
				validated_data.get("publication_date")
			),
			logo=self._validate_url(
				self._strip_string(validated_data.get("logo"))
			),
		)

		publisher = validated_data.get("publisher")
		if isinstance(publisher, dict):
			software.publisher = self._get_or_create_org(publisher)

		license_name = validated_data.get("license")
		if license_name:
			normalized = self._normalize_term(license_name, "license")
			license_obj = License.objects.filter(name__iexact=normalized).first()
			if not license_obj:
				raise serializers.ValidationError({"license": f"Unknown license '{license_name}'."})
			software.license = license_obj

		development_status = validated_data.get("development_status")
		if development_status:
			software.development_status = self._get_controlled_item(RepoStatus, development_status)

		software.save()

		submitters = [
			self._get_or_create_submitter(item) 
			for item in validated_data.get("submitter", [])
		]
		authors = [
			self._get_or_create_person(item) 
			for item in validated_data.get("authors", [])
		]
		for author, author_data in zip(authors, validated_data.get("authors", []), strict=False):
			affiliations = author_data.get("affiliation") or []
			if isinstance(affiliations, list):
				for org_data in affiliations:
					if not isinstance(org_data, dict):
						raise serializers.ValidationError({"affiliation": "Expected an object."})
					author.affiliation.add(self._get_or_create_org(org_data))

		submission_info = SubmissionInfo.objects.create(
			software=software,
			submission_date=timezone.now(),
		)
		if submitters:
			submission_info.submitter.set(submitters)

		if authors:
			software.authors.set(authors)

		if validated_data.get("programming_language"):
			prog_langs = [
				self._get_controlled_item(ProgrammingLanguage, item)
				for item in validated_data.get("programming_language", [])
			]
			software.programming_language.set(prog_langs)

		if validated_data.get("input_formats"):
			formats = [
				self._get_controlled_item(FileFormat, item)
				for item in validated_data.get("input_formats", [])
			]
			software.input_formats.set(formats)

		if validated_data.get("output_formats"):
			formats = [
				self._get_controlled_item(FileFormat, item)
				for item in validated_data.get("output_formats", [])
			]
			software.output_formats.set(formats)

		if validated_data.get("operating_system"):
			operating_systems = [
				self._get_controlled_item(OperatingSystem, item)
				for item in validated_data.get("operating_system", [])
			]
			software.operating_system.set(operating_systems)

		if validated_data.get("cpu_architecture"):
			architectures = [
				self._get_controlled_item(CpuArchitecture, item)
				for item in validated_data.get("cpu_architecture", [])
			]
			software.cpu_architecture.set(architectures)

		if validated_data.get("software_functionality"):
			functionality = [
				self._get_graph_list_item(FunctionCategory, item)
				for item in validated_data.get("software_functionality", [])
			]
			software.software_functionality.set(functionality)

		if validated_data.get("related_region"):
			regions = [
				self._get_graph_list_item(Region, item)
				for item in validated_data.get("related_region", [])
			]
			software.related_region.set(regions)

		if validated_data.get("related_phenomena"):
			phenomena = [
				self._get_graph_list_item(Phenomena, item)
				for item in validated_data.get("related_phenomena", [])
			]
			software.related_phenomena.set(phenomena)

		if validated_data.get("data_sources"):
			data_sources = [
				self._get_controlled_item(DataInput, item)
				for item in validated_data.get("data_sources", [])
			]
			software.data_sources.set(data_sources)

		if validated_data.get("keywords"):
			keywords = [
				self._get_or_create_keyword(item)
				for item in validated_data.get("keywords", [])
			]
			software.keywords.set(keywords)

		if validated_data.get("related_instruments"):
			instruments = [
				self._get_or_create_observatory(item, InstrObsType.INSTRUMENT)
				for item in validated_data.get("related_instruments", [])
			]
			software.related_instruments.set(instruments)

		if validated_data.get("related_observatories"):
			observatories = [
				self._get_or_create_observatory(item, InstrObsType.OBSERVATORY)
				for item in validated_data.get("related_observatories", [])
			]
			software.related_observatories.set(observatories)

		if validated_data.get("reference_publication"):
			reference = self._get_or_create_related(
				validated_data.get("reference_publication"),
				RelatedItemType.PUBLICATION,
			)
			software.reference_publication = reference

		if validated_data.get("related_publications"):
			publications = [
				self._get_or_create_related(url, RelatedItemType.PUBLICATION)
				for url in validated_data.get("related_publications", [])
			]
			software.related_publications.set(publications)

		if validated_data.get("related_datasets"):
			datasets = [
				self._get_or_create_related(url, RelatedItemType.DATASET)
				for url in validated_data.get("related_datasets", [])
			]
			software.related_datasets.set(datasets)

		if validated_data.get("related_software"):
			related = [
				self._get_or_create_related(url, RelatedItemType.SOFTWARE)
				for url in validated_data.get("related_software", [])
			]
			software.related_software.set(related)

		if validated_data.get("interoperable_software"):
			interop = [
				self._get_or_create_related(url, RelatedItemType.SOFTWARE)
				for url in validated_data.get("interoperable_software", [])
			]
			software.interoperable_software.set(interop)

		if validated_data.get("funder"):
			funders = [
				self._get_or_create_org(item)
				for item in validated_data.get("funder", [])
			]
			software.funder.set(funders)

		if validated_data.get("award"):
			awards = [
				self._get_or_create_award(item)
				for item in validated_data.get("award", [])
			]
			software.award.set(awards)

		version = validated_data.get("version")
		if isinstance(version, dict):
			version_obj = SoftwareVersion.objects.create(
				number=self._normalize_term(version.get("number"), "version_number"),
				release_date=self._validate_date(version.get("release_date")),
				description=self._strip_string(version.get("description")),
				version_pid=self._validate_url(self._strip_string(version.get("version_pid"))),
			)
			software.version.set([version_obj])

		software.save()
		return software

	def create(self, validated_data):
		print("CREATE")
		print(self.context)
		print(self._view)
		print(self.view())
		return super().create(validated_data)

	class Meta(HssiSerializer.Meta):
		model = Software
		fields = "__all__"
