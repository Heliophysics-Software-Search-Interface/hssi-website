"""Serializers for Software-related models."""

from typing import Any, Iterable

from django.http import HttpRequest
from django.db.models import Model, Manager

from .util import HssiSerializer, get_registered_serializer
from ..organizations import Organization
from ..people import Person
from ..related import RelatedItem, RelatedItemType
from ..software import Software, SoftwareVersion
from ..vocab import InstrObsType, InstrumentObservatory
from ..base import HssiModel
from ...admin.fetch_vocab import (
	URL_DATAINPUTS, URL_SUPPORTEDFILEFORMATS, URL_FUNCTIONCATEGORIES,
	URL_PHENOMENA,
)

NAME_UNKOWN = "UNKNOWN"

def serialize_obj_userfriendly(obj: Model) -> str | dict[str, Any]:
	"""Serialize a model object using its serializer or fall back to str()."""
	serializer_cls = get_registered_serializer(obj.__class__)
	if serializer_cls:
		return serializer_cls(obj).data
	if isinstance(obj, HssiModel):
		return obj.to_user_str()
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
			data[field.name] = [serialize_obj_userfriendly(item) for item in related]
			continue
		if field.many_to_one:
			related = getattr(obj, field.name)
			data[field.name] = serialize_obj_userfriendly(related) if related else None
			continue
		data[field.name] = getattr(obj, field.name)
	return data

class SoftwareSerializer(HssiSerializer):
	"""Serializer for Software model data."""

	def to_representation_user(self, instance) -> dict[str, Any]:
		"""
		User friendly view for Software model - serialize all non-null 
		fields and resolve foreign relations.
		"""
		data: dict[str, Any] = super().to_representation_standard(instance)
		for key, _ in data.items():
			value = getattr(instance, key)
			if isinstance(value, Model):
				data[key] = serialize_obj_userfriendly(value)
			if isinstance(value, Manager):
				assert(isinstance(value, Manager))
				new_value = []
				for item in value.all():
					new_item = serialize_obj_userfriendly(item)
					new_value.append(new_item)
				data[key] = new_value

		return {
			key: val 
			for key, val in data.items()
			if val
		}

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
		if not item.identifier and item.name == NAME_UNKOWN:
			return None
		if item.type == InstrObsType.OBSERVATORY:
			item_type = ["ResearchProject", "prov:Entity", "sosa:Platform"]
		else:
			item_type = ["IndividualProduct", "prov:Entity", "sosa:System"]
		data: dict[str, Any] = {
			"@type": item_type,
			"description": description,
		}
		if item.name != NAME_UNKOWN:
			data["name"] = item.name
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

	def _mentions_related(self, item: RelatedItem, description: str) -> dict[str, Any] | None:
		if not item.identifier and item.name == NAME_UNKOWN:
			return None
		type_map = {
			RelatedItemType.SOFTWARE: "SoftwareSourceCode",
			RelatedItemType.DATASET: "Dataset",
			RelatedItemType.PUBLICATION: "ScholarlyArticle",
		}
		data: dict[str, Any] = {
			"@type": type_map.get(item.type, "CreativeWork"),
			"description": description,
		}
		if item.name != NAME_UNKOWN:
			data["name"] = item.name
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
			"dateModified": "2025-03-05T12:34:56",
			"encodingFormat": "application/json",
			"name": "HSSI metadata describing the software",
			"description": "HSSI metadata describing the software",
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
		mentions = filter(lambda item: item is not None, mentions)

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

		return {
			key: value
			for key, value in data.items()
			if value
		}

	class Meta(HssiSerializer.Meta):
		model = Software
		fields = "__all__"
