"""Serializers for Software-related models."""

from typing import Any, Iterable

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.http import HttpRequest
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import serializers

from ..license import License
from ..organizations import Organization, Award
from ..people import Person, Submitter
from ..related import RelatedItem, RelatedItemType
from ..software import Software, SubmissionInfo, SoftwareVersion
from ..vocab import (
	CpuArchitecture,
	DataInput,
	FileFormat,
	FunctionCategory,
	InstrObsType,
	InstrumentObservatory,
	Keyword,
	OperatingSystem,
	Phenomena,
	ProgrammingLanguage,
	Region,
	RepoStatus,
)
from .util import HssiSerializer
from ...admin.fetch_vocab import (
	URL_DATAINPUTS, URL_SUPPORTEDFILEFORMATS, URL_FUNCTIONCATEGORIES,
	URL_PHENOMENA,
)


class SoftwareSerializer(HssiSerializer):
	"""Serializer for Software model data."""

	def _as_list(self, items: Iterable[Any]) -> list[Any]:
		return [item for item in items if item is not None]

	def _maybe_single(self, items: list[Any]) -> Any:
		if not items:
			return None
		if len(items) == 1:
			return items[0]
		return items

	def _registry_property_id(self, identifier: str | None) -> str | None:
		if not identifier:
			return None
		if "orcid.org" in identifier:
			return "https://registry.identifiers.org/registry/orcid"
		if "ror.org" in identifier:
			return "https://registry.identifiers.org/registry/ror"
		if "doi.org" in identifier:
			return "https://registry.identifiers.org/registry/doi"
		return None

	def _registry_value(self, identifier: str | None) -> str | None:
		if not identifier:
			return None
		if "orcid.org/" in identifier:
			return f"orcid:{identifier.split('orcid.org/')[-1]}"
		if "ror.org/" in identifier:
			return f"ror:{identifier.split('ror.org/')[-1]}"
		if "doi.org/" in identifier:
			return f"doi:{identifier.split('doi.org/')[-1]}"
		return identifier

	def _property_value(
		self, 
		identifier: str | None, 
		name: str | None = None
	) -> dict[str, Any] | None:
		if not identifier:
			return None
		value = self._registry_value(identifier)
		property_id = self._registry_property_id(identifier)
		data: dict[str, Any] = {
			"@id": identifier,
			"@type": "PropertyValue",
			"url": identifier,
		}
		if property_id:
			data["propertyID"] = property_id
		if value:
			data["value"] = value
		if name:
			data["name"] = name
		return data

	def _organization_jsonld(self, org: Organization | None) -> dict[str, Any] | None:
		if org is None:
			return None
		data: dict[str, Any] = {
			"@type": "Organization",
			"name": org.name,
		}
		if org.identifier:
			data["@id"] = org.identifier
			data["identifier"] = self._property_value(org.identifier)
		if org.website:
			data["url"] = org.website
		return data

	def _person_jsonld(self, person: Person) -> dict[str, Any]:
		data: dict[str, Any] = {
			"@type": "Person",
			"givenName": person.given_name,
			"familyName": person.family_name,
		}
		if person.identifier:
			data["@id"] = person.identifier
			data["identifier"] = self._property_value(person.identifier)
		affiliations = self._as_list(
			self._organization_jsonld(org) for org in person.affiliation.all()
		)
		if affiliations:
			data["affiliation"] = self._maybe_single(affiliations)
		return data

	def _author_list(self, instance: Software) -> dict[str, Any] | None:
		authors = self._as_list(
			self._person_jsonld(person) for person in instance.authors.all()
		)
		if not authors:
			return None
		return {"@list": authors}

	def _latest_version(self, instance: Software) -> SoftwareVersion | None:
		versions = list(instance.version.all())
		if not versions:
			return None
		with_dates = [v for v in versions if v.release_date]
		if with_dates:
			return max(with_dates, key=lambda v: v.release_date)
		return sorted(versions, key=lambda v: v.number)[-1]

	def _functionality_categories(self, instance: Software) -> tuple[list[str], list[str]]:
		categories: set[str] = set()
		subcategories: list[str] = []
		for func in instance.software_functionality.all():
			if not func.parent_nodes.exists():
				categories.add(func.name)
				continue
			subcategories.append(func.get_full_name())
			for parent in func.parent_nodes.all():
				categories.add(parent.name)
		print(sorted(categories), subcategories)
		return sorted(categories), subcategories

	def _defined_term(
		self, 
		name: str, 
		description: str | None = None, 
		in_set: str | None = None
	) -> dict[str, Any]:
		data: dict[str, Any] = {
			"@type": "DefinedTerm",
			"name": name,
		}
		if description:
			data["description"] = description
		if in_set:
			data["inDefinedTermSet"] = in_set
		return data

	def _mentions_instrument(self, item: InstrumentObservatory, description: str) -> dict[str, Any]:
		if item.type == InstrObsType.OBSERVATORY:
			item_type = ["ResearchProject", "prov:Entity", "sosa:Platform"]
		else:
			item_type = ["IndividualProduct", "prov:Entity", "sosa:System"]
		data: dict[str, Any] = {
			"@type": item_type,
			"description": description,
			"name": item.name,
		}
		if item.identifier:
			data["@id"] = item.identifier
			data["url"] = item.identifier
			if item.identifier.startswith("spase://"):
				data["identifier"] = {
					"@type": "PropertyValue",
					"propertyID": "SPASE Resource ID",
					"value": item.identifier,
				}
		return data

	def _mentions_related(self, item: RelatedItem, description: str) -> dict[str, Any]:
		type_map = {
			RelatedItemType.SOFTWARE: "SoftwareSourceCode",
			RelatedItemType.DATASET: "Dataset",
			RelatedItemType.PUBLICATION: "ScholarlyArticle",
		}
		data: dict[str, Any] = {
			"@type": type_map.get(item.type, "CreativeWork"),
			"description": description,
			"name": item.name,
		}
		if item.identifier:
			data["@id"] = item.identifier
			data["url"] = item.identifier
		else:
			data["disambiguatingDescription"] = item.name
		return data

	def _reference_publication(self, item: RelatedItem | None) -> dict[str, Any] | None:
		if not item:
			return None
		if not item.identifier:
			return None
		data: dict[str, Any] = {
			"@id": item.identifier,
			"@type": "ScholarlyWork",
		}
		if item.name:
			data["name"] = item.name
		return data

	def _subject_of(self, instance: Software) -> dict[str, Any] | None:
		version: SoftwareVersion | None = instance.version.first()
		if not version:
			return None
		content_url = None
		request: HttpRequest | None = self.context.get("request")
		if request:
			content_url = request.build_absolute_uri(instance.get_absolute_url())
		else:
			content_url = instance.get_absolute_url()
		data: dict[str, Any] = {
			"@type": "DataDownload",
			"contentUrl": content_url,
			"encodingFormat": "application/json",
			"name": instance.software_name,
			"description": instance.description,
		}
		if version.release_date:
			data["dateModified"] = version.release_date.isoformat()
		return data

	def to_representation_jsonld(self, instance: Software) -> dict[str, Any]:

		authors = self._author_list(instance)
		categories, subcategories = self._functionality_categories(instance)
		latest_version = self._latest_version(instance)

		keywords: list[dict[str, Any]] = []
		keywords += [
			self._defined_term(item.name, "dataSources", URL_DATAINPUTS)
			for item in instance.data_sources.all()
		]
		keywords += [
			self._defined_term(item.name, "inputFormats", URL_SUPPORTEDFILEFORMATS)
			for item in instance.input_formats.all()
		]
		keywords += [
			self._defined_term(item.name, "outputFormats", URL_SUPPORTEDFILEFORMATS)
			for item in instance.output_formats.all()
		]
		keywords += [
			self._defined_term(item.name, "relatedPhenomena", URL_PHENOMENA)
			for item in instance.related_phenomena.all()
		]
		keywords += [
			self._defined_term(item.name, "softwareFunctionality", URL_FUNCTIONCATEGORIES)
			for item in instance.software_functionality.all()
		]
		keywords += [self._defined_term(item.name) for item in instance.keywords.all()]

		mentions: list[dict[str, Any]] = []
		mentions += [
			self._mentions_instrument(item, "relatedInstruments")
			for item in instance.related_instruments.all()
		]
		mentions += [
			self._mentions_instrument(item, "relatedObservatories")
			for item in instance.related_observatories.all()
		]
		mentions += [
			self._mentions_related(item, "relatedPublications")
			for item in instance.related_publications.all()
		]
		mentions += [
			self._mentions_related(item, "relatedDatasets")
			for item in instance.related_datasets.all()
		]
		mentions += [
			self._mentions_related(item, "relatedSoftware")
			for item in instance.related_software.all()
		]
		mentions += [
			self._mentions_related(item, "interoperableSoftware")
			for item in instance.interoperable_software.all()
		]

		operating_systems = [item.name for item in instance.operating_system.all()]
		programming_languages = [str(item) for item in instance.programming_language.all()]
		processor_requirements = [item.name for item in instance.cpu_architecture.all()]

		spatial_coverage = [
			{
				"@type": "Place",
				"name": item.name,
				"keywords": self._defined_term(
					item.name,
					"RelatedRegion",
					item.identifier,
				),
			}
			for item in instance.related_region.all()
		]

		funding_item: dict[str, Any] = {}
		for award in instance.award.all():
			grant: dict[str, Any] = {
				"@type": "MonetaryGrant",
				"name": award.name,
			}
			funding_item["@type"] = "MonetaryGrant"
			funding_item["name"] = award.name
			if award.identifier:
				grant["identifier"] = award.identifier
			if award.funder:
				grant["funder"] = self._organization_jsonld(award.funder)
			break
		if not funding_item or not "funder" in funding_item:
			for funder in instance.funder.all():
				funding_item["@type"] = "MonetaryGrant"
				funding_item["funder"] = self._organization_jsonld(funder)

		data: dict[str, Any] = {
			"@context": {
				"@vocab": "https://schema.org/",
				"prov": "http://www.w3.org/ns/prov#",
				"sosa": "https://w3c.github.io/sdw-sosa-ssn/ssn/#SOSA",
				"codemeta": "https://github.com/codemeta/codemeta/blob/master/codemeta.jsonld",
			},
			"@id": instance.persistent_identifier or instance.get_absolute_url(),
			"@type": ["SoftwareSourceCode", "SoftwareApplication"],
			"name": instance.software_name,
			"description": instance.description,
			"codeRepository": instance.code_repository_url,
			"image": instance.logo,
			"datePublished": instance.publication_date,
			"applicationCategory": categories,
			"applicationSubCategory": subcategories,
			"author": authors,
			"codemeta:buildInstructions": instance.documentation,
			"codemeta:referencePublication": self._reference_publication(instance.reference_publication),
			"codemeta:developmentStatus": (
				instance.development_status.name
				if instance.development_status else None
			),
			"creativeWorkStatus": (
				{
					"@id": instance.development_status.identifier,
					"@type": "DefinedTerm",
					"name": instance.development_status.name,
					"description": instance.development_status.definition,
					"inDefinedTermSet": "https://www.repostatus.org",
					"image": instance.development_status.image,
				}
				if instance.development_status else None
			),
			"identifier": self._property_value(
				instance.persistent_identifier,
				name=(
					f"DOI: {instance.persistent_identifier.split('doi.org/')[-1]}"
					if instance.persistent_identifier and "doi.org/" in instance.persistent_identifier
					else None
				),
			),
			"license": (
				{
					"@id": instance.license.url,
					"@type": "CreativeWork",
					"name": instance.license.name,
					"url": instance.license.url,
				}
				if instance.license and instance.license.url else None
			),
			"keywords": keywords or None,
			"mentions": mentions or None,
			"operatingSystem": self._maybe_single(operating_systems),
			"programmingLanguage": self._maybe_single(programming_languages),
			"processorRequirements": processor_requirements or None,
			"publisher": self._organization_jsonld(instance.publisher),
			"softwareVersion": latest_version.number if latest_version else None,
			"version": latest_version.number if latest_version else None,
			"spatialCoverage": spatial_coverage or None,
			"funding": funding_item or None,
			"subjectOf": self._subject_of(instance),
		}

		return {key: value for key, value in data.items() if value not in (None, [], {})}

	def _strip_string(self, value: Any) -> str | None:
		if value is None:
			return None
		if not isinstance(value, str):
			raise serializers.ValidationError("Expected a string.")
		return value.strip()

	def _validate_url(self, value: str | None, field_name: str) -> str | None:
		if value is None or value == "":
			return None
		validator = URLValidator()
		try:
			validator(value)
		except DjangoValidationError as exc:
			raise serializers.ValidationError({field_name: str(exc)})
		return value

	def _validate_date(self, value: str | None, field_name: str):
		if value is None or value == "":
			return None
		if not isinstance(value, str):
			raise serializers.ValidationError({field_name: "Expected a date string."})
		parsed = parse_date(value)
		if parsed is None:
			raise serializers.ValidationError({field_name: "Invalid date format."})
		return parsed

	def _normalize_term(self, value: str, field_name: str) -> str:
		if not isinstance(value, str):
			raise serializers.ValidationError({field_name: "Expected a string."})
		normalized = value.strip()
		if not normalized:
			raise serializers.ValidationError({field_name: "Value cannot be empty."})
		return normalized

	def _get_graph_list(self, model, value: str, field_name: str):
		normalized = self._normalize_term(value, field_name)
		if ":" not in normalized:
			obj = model.objects.filter(name__iexact=normalized).first()
			if not obj:
				raise serializers.ValidationError({field_name: f"Unknown value '{value}'."})
			return obj

		parts = [part.strip() for part in normalized.split(":")]
		parent = model.objects.filter(name__iexact=parts[0], parent_nodes__isnull=True).first()
		if not parent:
			raise serializers.ValidationError({field_name: f"Unknown value '{value}'."})
		for part in parts[1:]:
			child = model.objects.filter(name__iexact=part, parent_nodes=parent).first()
			if not child:
				raise serializers.ValidationError({field_name: f"Unknown value '{value}'."})
			parent = child
		return parent

	def _get_controlled(self, model, value: str, field_name: str):
		normalized = self._normalize_term(value, field_name)
		obj = model.objects.filter(name__iexact=normalized).first()
		if not obj:
			raise serializers.ValidationError({field_name: f"Unknown value '{value}'."})
		return obj

	def _get_or_create_keyword(self, value: str):
		normalized = self._normalize_term(value, "keywords")
		obj = Keyword.objects.filter(name__iexact=normalized).first()
		if obj:
			return obj
		return Keyword.objects.create(name=normalized)

	def _get_or_create_person(self, data: dict[str, Any]) -> Person:
		given_name = self._normalize_term(data.get("given_name"), "givenName")
		family_name = self._normalize_term(data.get("family_name"), "familyName")
		identifier = data.get("identifier")
		if identifier:
			identifier = self._validate_url(self._strip_string(identifier), "identifier")
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
			given_name__iexact=given_name,
			family_name__iexact=family_name,
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
			identifier = self._validate_url(self._strip_string(identifier), "identifier")
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

	def _get_or_create_instrument(self, data: dict[str, Any], instr_type: InstrObsType) -> InstrumentObservatory:
		name = self._normalize_term(data.get("name"), "name")
		identifier = data.get("identifier")
		if identifier:
			identifier = self._validate_url(self._strip_string(identifier), "identifier")
			entry = InstrumentObservatory.objects.filter(identifier=identifier).first()
			if entry:
				return entry
			return InstrumentObservatory.objects.create(
				name=name,
				identifier=identifier,
				type=instr_type,
			)
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
		identifier = self._validate_url(self._normalize_term(url, "identifier"), "identifier")
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
			if field not in data or data[field] in (None, "", []):
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

		self._validate_url(self._strip_string(data.get("code_repository_url")), "codeRepositoryUrl")
		self._validate_url(self._strip_string(data.get("documentation")), "documentation")
		self._validate_url(self._strip_string(data.get("persistent_identifier")), "persistentIdentifier")
		self._validate_url(self._strip_string(data.get("reference_publication")), "referencePublication")
		self._validate_url(self._strip_string(data.get("logo")), "logo")

		if data.get("publication_date"):
			self._validate_date(data.get("publication_date"), "publicationDate")

		concise_description = data.get("concise_description")
		if concise_description is not None:
			concise_description = self._strip_string(concise_description) or ""
			if len(concise_description) > 200:
				raise serializers.ValidationError({"conciseDescription": "Must be 200 characters or fewer."})

		version = data.get("version")
		if version is not None:
			if not isinstance(version, dict):
				raise serializers.ValidationError({"version": "Expected an object."})
			self._normalize_term(version.get("number"), "version.number")
			if version.get("release_date"):
				self._validate_date(version.get("release_date"), "version.releaseDate")
			if version.get("version_pid"):
				self._validate_url(self._strip_string(version.get("version_pid")), "version.versionPid")

		return data

	@transaction.atomic
	def create_user(self, validated_data: dict[str, Any]):
		software = Software.objects.create(
			software_name=self._normalize_term(validated_data.get("software_name"), "softwareName"),
			code_repository_url=self._validate_url(self._strip_string(validated_data.get("code_repository_url")), "codeRepositoryUrl"),
			description=self._normalize_term(validated_data.get("description"), "description"),
			concise_description=self._strip_string(validated_data.get("concise_description")),
			documentation=self._validate_url(self._strip_string(validated_data.get("documentation")), "documentation"),
			persistent_identifier=self._validate_url(self._strip_string(validated_data.get("persistent_identifier")), "persistentIdentifier"),
			publication_date=self._validate_date(validated_data.get("publication_date"), "publicationDate"),
			logo=self._validate_url(self._strip_string(validated_data.get("logo")), "logo"),
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
			software.development_status = self._get_controlled(RepoStatus, development_status, "developmentStatus")

		software.save()

		submitters = [self._get_or_create_submitter(item) for item in validated_data.get("submitter", [])]
		authors = [self._get_or_create_person(item) for item in validated_data.get("authors", [])]
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
				self._get_controlled(ProgrammingLanguage, item, "programmingLanguage")
				for item in validated_data.get("programming_language", [])
			]
			software.programming_language.set(prog_langs)

		if validated_data.get("input_formats"):
			formats = [
				self._get_controlled(FileFormat, item, "inputFormats")
				for item in validated_data.get("input_formats", [])
			]
			software.input_formats.set(formats)

		if validated_data.get("output_formats"):
			formats = [
				self._get_controlled(FileFormat, item, "outputFormats")
				for item in validated_data.get("output_formats", [])
			]
			software.output_formats.set(formats)

		if validated_data.get("operating_system"):
			operating_systems = [
				self._get_controlled(OperatingSystem, item, "operatingSystem")
				for item in validated_data.get("operating_system", [])
			]
			software.operating_system.set(operating_systems)

		if validated_data.get("cpu_architecture"):
			architectures = [
				self._get_controlled(CpuArchitecture, item, "cpuArchitecture")
				for item in validated_data.get("cpu_architecture", [])
			]
			software.cpu_architecture.set(architectures)

		if validated_data.get("software_functionality"):
			functionality = [
				self._get_graph_list(FunctionCategory, item, "softwareFunctionality")
				for item in validated_data.get("software_functionality", [])
			]
			software.software_functionality.set(functionality)

		if validated_data.get("related_region"):
			regions = [
				self._get_graph_list(Region, item, "relatedRegion")
				for item in validated_data.get("related_region", [])
			]
			software.related_region.set(regions)

		if validated_data.get("related_phenomena"):
			phenomena = [
				self._get_graph_list(Phenomena, item, "relatedPhenomena")
				for item in validated_data.get("related_phenomena", [])
			]
			software.related_phenomena.set(phenomena)

		if validated_data.get("data_sources"):
			data_sources = [
				self._get_controlled(DataInput, item, "dataSources")
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
				self._get_or_create_instrument(item, InstrObsType.INSTRUMENT)
				for item in validated_data.get("related_instruments", [])
			]
			software.related_instruments.set(instruments)

		if validated_data.get("related_observatories"):
			observatories = [
				self._get_or_create_instrument(item, InstrObsType.OBSERVATORY)
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
				number=self._normalize_term(version.get("number"), "version.number"),
				release_date=self._validate_date(version.get("release_date"), "version.releaseDate"),
				description=self._strip_string(version.get("description")),
				version_pid=self._validate_url(self._strip_string(version.get("version_pid")), "version.versionPid"),
			)
			software.version.set([version_obj])

		software.save()
		return software

	class Meta(HssiSerializer.Meta):
		model = Software
		fields = "__all__"
