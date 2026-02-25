import json
from datetime import date

from django.conf import settings
from django.db import transaction
from django.http import (
	HttpRequest, JsonResponse, HttpResponseBadRequest,
	HttpResponseForbidden, HttpResponseNotAllowed,
)
from django.views.decorators.csrf import csrf_exempt

from ..models import Software, VisibleSoftware
from ..forms.names import *
from ..data_parser import (
	api_submission_to_formdict,
	apply_software_core_fields_partial,
	apply_reference_publication,
	apply_development_status,
	apply_logo,
	apply_license,
	apply_publisher,
	apply_version,
	apply_authors,
	apply_publication_date,
	apply_controlled_m2m,
	apply_function_category,
	apply_keywords,
	apply_awards,
	apply_funders,
	apply_related_items,
	apply_related_instruments,
	apply_related_observatories,
	ProgrammingLanguage, DataInput, FileFormat, CpuArchitecture,
	OperatingSystem, Region, Phenomena, RelatedItemType,
)


def _check_bearer_token(request: HttpRequest) -> str | None:
	"""Validate Authorization: Bearer <token>. Returns error message or None."""
	token = settings.HSSI_UPDATE_TOKEN
	if not token:
		return "Update API is not configured (no HSSI_UPDATE_TOKEN in settings)."

	auth_header = request.META.get("HTTP_AUTHORIZATION", "")
	if not auth_header.startswith("Bearer "):
		return "Missing or malformed Authorization header. Expected: Bearer <token>"

	provided_token = auth_header[len("Bearer "):]
	if provided_token != token:
		return "Invalid bearer token."

	return None


def _get_visible_software(software_id: str) -> tuple[Software | None, str | None]:
	"""Look up a VisibleSoftware by UUID. Returns (software, error_message)."""
	try:
		vs = VisibleSoftware.objects.get(pk=software_id)
	except VisibleSoftware.DoesNotExist:
		return None, f"No visible software found with ID '{software_id}'."
	except Exception as exc:
		return None, f"Invalid software ID: {exc}"

	software = Software.objects.get(pk=vs.pk)
	return software, None


# Field key → apply function mapping for partial updates.
# Each entry is (apply_fn, requires_save_first) where requires_save_first
# indicates whether the software object must be saved before calling apply_fn
# (needed for M2M fields).
SCALAR_FIELD_APPLIERS = {
	FIELD_REFERENCEPUBLICATION: apply_reference_publication,
	FIELD_DEVELOPMENTSTATUS: apply_development_status,
	FIELD_LOGO: apply_logo,
	FIELD_PUBLICATIONDATE: apply_publication_date,
}

# These require software.save() before they can be applied (M2M fields).
M2M_FIELD_APPLIERS = {
	FIELD_AUTHORS: apply_authors,
	FIELD_KEYWORDS: apply_keywords,
	FIELD_AWARDTITLE: apply_awards,
	FIELD_FUNDER: apply_funders,
	FIELD_RELATEDINSTRUMENTS: apply_related_instruments,
	FIELD_RELATEDOBSERVATORIES: apply_related_observatories,
}

# Core scalar fields handled by apply_software_core_fields_partial
CORE_FIELDS = {
	FIELD_PERSISTENTIDENTIFIER, FIELD_CODEREPOSITORYURL,
	FIELD_SOFTWARENAME, FIELD_DESCRIPTION,
	FIELD_CONCISEDESCRIPTION, FIELD_DOCUMENTATION,
}

# Nested object fields with their own apply functions
NESTED_FIELD_APPLIERS = {
	FIELD_LICENSE: apply_license,
	FIELD_PUBLISHER: apply_publisher,
	FIELD_VERSIONNUMBER: apply_version,
}

# Controlled-list M2M fields: (model_class, m2m_attr, allow_creation)
CONTROLLED_M2M_FIELDS = {
	FIELD_PROGRAMMINGLANGUAGE: (ProgrammingLanguage, FIELD_PROGRAMMINGLANGUAGE, False),
	FIELD_DATASOURCES: (DataInput, FIELD_DATASOURCES, False),
	FIELD_INPUTFORMATS: (FileFormat, FIELD_INPUTFORMATS, False),
	FIELD_OUTPUTFORMATS: (FileFormat, FIELD_OUTPUTFORMATS, False),
	FIELD_CPUARCHITECTURE: (CpuArchitecture, FIELD_CPUARCHITECTURE, False),
	FIELD_OPERATINGSYSTEM: (OperatingSystem, FIELD_OPERATINGSYSTEM, False),
	FIELD_RELATEDREGION: (Region, FIELD_RELATEDREGION, False),
	FIELD_RELATEDPHENOMENA: (Phenomena, FIELD_RELATEDPHENOMENA, False),
}

# Related item M2M fields: (m2m_attr, item_type)
RELATED_ITEM_FIELDS = {
	FIELD_RELATEDPUBLICATIONS: (FIELD_RELATEDPUBLICATIONS, RelatedItemType.PUBLICATION),
	FIELD_RELATEDDATASETS: (FIELD_RELATEDDATASETS, RelatedItemType.DATASET),
	FIELD_RELATEDSOFTWARE: (FIELD_RELATEDSOFTWARE, RelatedItemType.SOFTWARE),
	FIELD_INTEROPERABLESOFTWARE: (FIELD_INTEROPERABLESOFTWARE, RelatedItemType.SOFTWARE),
}


@csrf_exempt
def api_update(request: HttpRequest):
	"""Partial update endpoint for VisibleSoftware entries.

	POST /api/update
	Authorization: Bearer <token>
	Content-Type: application/json

	{
		"softwareId": "uuid-of-visible-software",
		"fields": { ... only the fields to update ... }
	}
	"""
	if request.method != "POST":
		return HttpResponseNotAllowed(["POST"])

	auth_error = _check_bearer_token(request)
	if auth_error:
		return HttpResponseForbidden(auth_error)

	try:
		encoding = request.encoding or "utf-8"
		body = json.loads(request.body.decode(encoding))
	except Exception as exc:
		return HttpResponseBadRequest(f"Invalid JSON body: {exc}")

	if not isinstance(body, dict):
		return HttpResponseBadRequest("Request body must be a JSON object.")

	software_id = body.get("softwareId")
	if not software_id:
		return HttpResponseBadRequest("Missing required field 'softwareId'.")

	fields_data = body.get("fields")
	if not isinstance(fields_data, dict) or not fields_data:
		return HttpResponseBadRequest("'fields' must be a non-empty object.")

	software, err = _get_visible_software(software_id)
	if err:
		return HttpResponseBadRequest(err)

	# Convert the partial fields dict into the form-compatible format that
	# the existing apply_* functions expect. We build a minimal item dict
	# and run it through api_submission_to_formdict's per-field logic.
	form_data = _convert_partial_fields(fields_data)

	fields_updated = []
	try:
		with transaction.atomic():
			# 1. Core scalar fields
			has_core = any(k in form_data for k in CORE_FIELDS)
			if has_core:
				apply_software_core_fields_partial(software, form_data)
				fields_updated.extend(k for k in CORE_FIELDS if k in form_data)

			# 2. Scalar FK fields
			for field_key, apply_fn in SCALAR_FIELD_APPLIERS.items():
				if field_key in form_data:
					apply_fn(software, form_data)
					fields_updated.append(field_key)

			# 3. Nested object fields (license, publisher, version)
			for field_key, apply_fn in NESTED_FIELD_APPLIERS.items():
				if field_key in form_data:
					apply_fn(software, form_data)
					fields_updated.append(field_key)

			# 4. licenseFileURL (simple scalar)
			if FIELD_LICENSEFILEURL in form_data:
				software.licenseFileUrl = form_data[FIELD_LICENSEFILEURL]
				fields_updated.append(FIELD_LICENSEFILEURL)

			# Save before M2M operations
			software.save()

			# 5. M2M fields with dedicated apply functions
			for field_key, apply_fn in M2M_FIELD_APPLIERS.items():
				if field_key in form_data:
					apply_fn(software, form_data)
					fields_updated.append(field_key)

			# 6. Software Functionality (special handling)
			if FIELD_SOFTWAREFUNCTIONALITY in form_data:
				func_values = form_data.get(FIELD_SOFTWAREFUNCTIONALITY, [])
				if func_values:
					apply_function_category(software, func_values)
				fields_updated.append(FIELD_SOFTWAREFUNCTIONALITY)

			# 7. Controlled-list M2M fields
			for field_key, (model_cls, m2m_attr, allow_create) in CONTROLLED_M2M_FIELDS.items():
				if field_key in form_data:
					apply_controlled_m2m(
						software, form_data,
						field_key, model_cls, m2m_attr,
						allow_creation=allow_create,
					)
					fields_updated.append(field_key)

			# 8. Related item M2M fields
			for field_key, (m2m_attr, item_type) in RELATED_ITEM_FIELDS.items():
				if field_key in form_data:
					apply_related_items(
						software, form_data.get(field_key),
						m2m_attr, item_type,
					)
					fields_updated.append(field_key)

			# Update dateModified on the existing SubmissionInfo
			if software.submissionInfo:
				software.submissionInfo.dateModified = date.today()
				software.submissionInfo.modificationDescription = (
					f"Partial update via API: {', '.join(fields_updated)}"
				)
				software.submissionInfo.save()

			software.save()

	except Exception as exc:
		return HttpResponseBadRequest(f"Update failed: {exc}")

	return JsonResponse({
		"status": "ok",
		"softwareId": str(software.id),
		"fieldsUpdated": fields_updated,
	})


def _convert_partial_fields(fields: dict) -> dict:
	"""Convert API-style partial fields dict into form-compatible dict.

	Reuses the same field name conventions as api_submission_to_formdict but
	only processes keys that are actually present.
	"""
	form: dict = {}

	# Simple string/URL fields pass through directly
	for key in (
		FIELD_PERSISTENTIDENTIFIER, FIELD_SOFTWARENAME, FIELD_DESCRIPTION,
		FIELD_CONCISEDESCRIPTION, FIELD_DOCUMENTATION, FIELD_DEVELOPMENTSTATUS,
		FIELD_REFERENCEPUBLICATION, FIELD_LICENSEFILEURL, FIELD_LOGO,
		FIELD_PUBLICATIONDATE,
	):
		if key in fields:
			form[key] = fields[key]

	# codeRepositoryUrl — API uses lowercase 'Url'
	if ROW_SOFTWARE_CODEREPOSITORYURL in fields:
		form[FIELD_CODEREPOSITORYURL] = fields[ROW_SOFTWARE_CODEREPOSITORYURL]
	elif FIELD_CODEREPOSITORYURL in fields:
		form[FIELD_CODEREPOSITORYURL] = fields[FIELD_CODEREPOSITORYURL]

	# Authors
	if FIELD_AUTHORS in fields:
		authors = fields[FIELD_AUTHORS]
		if isinstance(authors, list):
			form_authors = []
			for author in authors:
				if not isinstance(author, dict):
					continue
				first = author.get("firstName", "")
				last = author.get("lastName", "")
				author_entry = {FIELD_AUTHORS: f"{first} {last}".strip()}
				ident = author.get(ROW_PERSON_IDENTIFIER)
				if ident:
					author_entry[FIELD_AUTHORIDENTIFIER] = ident
				affiliations = author.get(ROW_PERSON_AFFILIATION, [])
				if isinstance(affiliations, list) and affiliations:
					affil_entries = []
					for affil in affiliations:
						if not isinstance(affil, dict):
							continue
						affil_name = affil.get(ROW_ORGANIZATION_NAME)
						if not affil_name:
							continue
						affil_entry = {FIELD_AUTHORAFFILIATION: affil_name}
						affil_ident = affil.get(ROW_ORGANIZATION_IDENTIFIER)
						if affil_ident:
							affil_entry[FIELD_AUTHORAFFILIATIONIDENTIFIER] = affil_ident
						affil_entries.append(affil_entry)
					if affil_entries:
						author_entry[FIELD_AUTHORAFFILIATION] = affil_entries
				form_authors.append(author_entry)
			form[FIELD_AUTHORS] = form_authors

	# Publisher
	if FIELD_PUBLISHER in fields:
		publisher = fields[FIELD_PUBLISHER]
		if isinstance(publisher, dict):
			form[FIELD_PUBLISHER] = {
				FIELD_PUBLISHER: publisher.get(ROW_ORGANIZATION_NAME, ""),
				FIELD_PUBLISHERIDENTIFIER: publisher.get(FIELD_PUBLISHERIDENTIFIER),
			}

	# License
	if FIELD_LICENSE in fields:
		license_field = fields[FIELD_LICENSE]
		if isinstance(license_field, str):
			form[FIELD_LICENSE] = {FIELD_LICENSE: license_field}
		elif isinstance(license_field, dict):
			form[FIELD_LICENSE] = {
				FIELD_LICENSE: license_field.get(ROW_LICENSE_NAME),
				FIELD_LICENSEURI: license_field.get(ROW_LICENSE_URL),
			}

	# Version
	if ROW_SOFTWARE_VERSION in fields:
		version = fields[ROW_SOFTWARE_VERSION]
		if isinstance(version, dict):
			form[FIELD_VERSIONNUMBER] = {
				FIELD_VERSIONNUMBER: version.get(ROW_VERSION_NUMBER),
				FIELD_VERSIONDATE: version.get(ROW_VERSION_DATE),
				FIELD_VERSIONDESCRIPTION: version.get(ROW_VERSION_DESCRIPTION),
				FIELD_VERSIONPID: version.get(ROW_VERSION_PID),
			}

	# Simple list fields pass through directly
	for key in (
		FIELD_PROGRAMMINGLANGUAGE, FIELD_SOFTWAREFUNCTIONALITY,
		FIELD_DATASOURCES, FIELD_INPUTFORMATS, FIELD_OUTPUTFORMATS,
		FIELD_CPUARCHITECTURE, FIELD_OPERATINGSYSTEM, FIELD_RELATEDREGION,
		FIELD_RELATEDPHENOMENA, FIELD_KEYWORDS,
		FIELD_RELATEDPUBLICATIONS, FIELD_RELATEDDATASETS,
		FIELD_RELATEDSOFTWARE, FIELD_INTEROPERABLESOFTWARE,
	):
		if key in fields:
			val = fields[key]
			form[key] = val if isinstance(val, list) else []

	# Related instruments
	if FIELD_RELATEDINSTRUMENTS in fields:
		relinstruments = fields[FIELD_RELATEDINSTRUMENTS]
		if isinstance(relinstruments, list):
			form_instrs = []
			for instr in relinstruments:
				if isinstance(instr, dict):
					form_instrs.append({
						FIELD_RELATEDINSTRUMENTS: instr.get(ROW_CONTROLLEDLIST_NAME),
						FIELD_RELATEDINSTRUMENTIDENTIFIER: instr.get(ROW_CONTROLLEDLIST_IDENTIFIER),
					})
			form[FIELD_RELATEDINSTRUMENTS] = form_instrs

	# Related observatories
	if FIELD_RELATEDOBSERVATORIES in fields:
		relobservatories = fields[FIELD_RELATEDOBSERVATORIES]
		if isinstance(relobservatories, list):
			form_obs = []
			for obs in relobservatories:
				if isinstance(obs, dict):
					form_obs.append({
						FIELD_RELATEDOBSERVATORIES: obs.get(ROW_CONTROLLEDLIST_NAME),
						FIELD_RELATEDOBSERVATORYIDENTIFIER: obs.get(ROW_CONTROLLEDLIST_IDENTIFIER),
					})
			form[FIELD_RELATEDOBSERVATORIES] = form_obs

	# Funders
	if FIELD_FUNDER in fields:
		funders = fields[FIELD_FUNDER]
		if isinstance(funders, list):
			form_funders = []
			for funder in funders:
				if isinstance(funder, dict):
					form_funders.append({
						FIELD_FUNDER: funder.get(ROW_ORGANIZATION_NAME),
						FIELD_FUNDERIDENTIFIER: funder.get(ROW_ORGANIZATION_IDENTIFIER),
					})
			form[FIELD_FUNDER] = form_funders

	# Awards
	if FIELD_AWARDTITLE in fields:
		awards = fields[FIELD_AWARDTITLE]
		if isinstance(awards, list):
			form_awards = []
			for award in awards:
				if isinstance(award, dict):
					form_awards.append({
						FIELD_AWARDTITLE: award.get(ROW_CONTROLLEDLIST_NAME),
						FIELD_AWARDNUMBER: award.get(ROW_CONTROLLEDLIST_IDENTIFIER),
					})
			form[FIELD_AWARDTITLE] = form_awards

	return form


@csrf_exempt
def api_update_lookup(request: HttpRequest):
	"""Lookup a VisibleSoftware entry by exact code repository URL.

	GET /api/update/lookup?repo_url=https://github.com/user/repo
	Authorization: Bearer <token>
	"""
	if request.method != "GET":
		return HttpResponseNotAllowed(["GET"])

	auth_error = _check_bearer_token(request)
	if auth_error:
		return HttpResponseForbidden(auth_error)

	repo_url = request.GET.get("repo_url", "").strip()
	if not repo_url:
		return HttpResponseBadRequest("Missing required parameter 'repo_url'.")

	# Normalize trailing slash for matching
	normalized = repo_url.rstrip("/")

	visible_ids = list(VisibleSoftware.objects.values_list("id", flat=True))
	if not visible_ids:
		return JsonResponse({"results": []})

	# Exact match on codeRepositoryUrl (try with and without trailing slash)
	matches = Software.objects.filter(
		id__in=visible_ids,
		codeRepositoryUrl__in=[normalized, normalized + "/", repo_url],
	)

	results = []
	for sw in matches:
		results.append({
			"softwareId": str(sw.id),
			"softwareName": sw.softwareName,
			"codeRepositoryUrl": sw.codeRepositoryUrl,
		})

	if len(results) == 1:
		return JsonResponse(results[0])

	return JsonResponse({"results": results})
