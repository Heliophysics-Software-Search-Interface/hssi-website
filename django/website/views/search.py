import re
import time

from django.db.models import Q
from django.http import HttpRequest, JsonResponse

from ..models import Software, VisibleSoftware


def build_field_query(query: str, tokens: list[str], fields: list[str]) -> Q:
	"""Build a case-insensitive OR query across fields for a query and tokens."""
	q = Q()
	for field in fields:
		if query:
			q |= Q(**{f"{field}__icontains": query})
		for token in tokens:
			q |= Q(**{f"{field}__icontains": token})
	return q

def search_visible_software(request: HttpRequest) -> JsonResponse:
	"""
	Search visible software by query terms and return ordered result IDs.

	Ranking is based on tiers: name/description first, then keywords, then
	regions/function/data sources, then other metadata fields.
	"""
	start_time = time.monotonic()
	query = (request.GET.get("q") or "").strip()
	if not query:
		return JsonResponse({"results": []})

	tokens = [token for token in re.split(r"\s+", query) if token]
	print(f"[search] query='{query}' tokens={tokens}")

	tier_1_fields = [
		"software_name",
		"concise_description",
		"description",
	]
	tier_2_fields = [
		"keywords__name",
	]
	tier_3_fields = [
		"related_region__name",
		"software_functionality__name",
		"data_sources__name",
		"related_phenomena__name",
	]
	tier_4_subtiers = [
		[
			"publisher__name",
			"publisher__abbreviation",
			"authors__given_name",
			"authors__family_name",
			"authors__identifier",
		],
		[
			"programming_language__name",
			"related_instruments__name",
			"related_instruments__abbreviation",
			"related_observatories__name",
		],
		[
			"related_observatories__abbreviation",
			"reference_publication__name",
			"related_publications__name",
		],
		[
			"related_datasets__name",
			"related_software__name",
			"interoperable_software__name",
		],
		[
			"funder__name",
			"funder__abbreviation",
			"award__name",
		],
		[
			"award__identifier",
			"input_formats__name",
			"input_formats__extension",
			"output_formats__name",
			"output_formats__extension",
		],
		[
			"cpu_architecture__name",
			"development_status__name",
			"operating_system__name",
			"license__name",
		],
		[
			"code_repository_url",
			"documentation",
		]
	]

	visible_ids = list(VisibleSoftware.objects.values_list("id", flat=True))
	base_qs = Software.objects.filter(id__in=visible_ids)

	def fetch_tier_ids(tier_name: str, fields: list[str]) -> list[str]:
		"""Fetch matching IDs for a tier and log its timing."""
		tier_start = time.monotonic()
		query_obj = build_field_query(query, tokens, fields)
		ids = list(
			base_qs.filter(query_obj)
			.distinct()
			.values_list("id", flat=True)
		)
		elapsed = time.monotonic() - tier_start
		print(f"[search] {tier_name} matches={len(ids)} elapsed={elapsed:.3f}s")
		return [str(uid) for uid in ids]

	tier_1_ids = fetch_tier_ids("tier_1", tier_1_fields)
	tier_2_ids = fetch_tier_ids("tier_2", tier_2_fields)
	tier_3_ids = fetch_tier_ids("tier_3", tier_3_fields)
	tier_4_ids: list[str] = []
	for index, fields in enumerate(tier_4_subtiers, start=1):
		subtier_ids = fetch_tier_ids(f"tier_4_{index}", fields)
		tier_4_ids.extend(subtier_ids)

	result_ids: list[str] = []
	seen: set[str] = set()
	for tier_ids in (tier_1_ids, tier_2_ids, tier_3_ids, tier_4_ids):
		for uid in tier_ids:
			if uid in seen:
				continue
			seen.add(uid)
			result_ids.append(uid)

	total_elapsed = time.monotonic() - start_time
	print(f"[search] total_results={len(result_ids)} elapsed={total_elapsed:.3f}s")
	return JsonResponse({"results": result_ids})
