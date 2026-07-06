import re
import time

from django.db.models import Q
from django.http import HttpRequest, JsonResponse

from ..models import Software, VerifiedSoftware
from ..models.people import Person
from ..models.serializers.software import SoftwareSerializer
from ..models.serializers.util import SerialView


# ---------------------------------------------------------------------------
# Field-search alias map
# Maps user-facing aliases to lists of ORM icontains lookup paths on Software.
# A value of None is a sentinel meaning "use build_author_query instead."
# ---------------------------------------------------------------------------

_FIELD_ALIAS_MAP: dict[str, list[str] | None] = {
    # Direct text / URL fields
    "name": ["software_name__icontains"],
    "description": ["description__icontains", "concise_description__icontains"],
    "repo": ["code_repository_url__icontains"],
    "docs": ["documentation__icontains"],
    "pid": ["persistent_identifier__icontains"],

    # Authors — special case (sentinel None)
    "author": None,

    # FK / M2M fields
    "publisher": ["publisher__name__icontains"],
    "keyword": ["keywords__name__icontains"],
    "lang": ["programming_language__name__icontains"],
    "license": ["license__name__icontains"],
    "region": ["related_region__name__icontains"],
    "phenomena": ["related_phenomena__name__icontains"],
    "instrument": ["related_instruments__name__icontains", "related_instruments__abbreviation__icontains"],
    "observatory": ["related_observatories__name__icontains", "related_observatories__abbreviation__icontains"],
    "funder": ["funder__name__icontains"],
    "award": ["award__name__icontains"],
    "status": ["development_status__name__icontains"],
    "os": ["operating_system__name__icontains"],
    "cpu": ["cpu_architecture__name__icontains"],
    "source": ["data_sources__name__icontains"],
    "function": ["software_functionality__name__icontains"],
    "input": ["input_formats__name__icontains", "input_formats__extension__icontains"],
    "output": ["output_formats__name__icontains", "output_formats__extension__icontains"],
    "publication": ["related_publications__name__icontains", "reference_publication__name__icontains"],
    "reference_publication": ["reference_publication__name__icontains"],
    "dataset": ["related_datasets__name__icontains"],
    "related": ["related_software__name__icontains"],
    "interoperable": ["interoperable_software__name__icontains"],
    "version": ["version__number__icontains"],
}

_FIELD_TOKEN_RE = re.compile(r'(\w+):"([^"]*)"')


def parse_field_queries(raw_query: str) -> tuple[list[tuple[str, str]], str]:
    """
    Extract field:"value" tokens from raw_query.
    Returns ([(alias, value), ...], remainder) where remainder is the raw
    query string with all matched tokens stripped out.
    """
    field_queries: list[tuple[str, str]] = []

    def collect(m: re.Match) -> str:
        field_queries.append((m.group(1).lower(), m.group(2)))
        return ""

    remainder = _FIELD_TOKEN_RE.sub(collect, raw_query).strip()
    return field_queries, remainder


def build_author_query(value: str) -> Q:
    """
    Build a Q for searching authors by name across given_name and family_name.
    For multi-word values, also matches same-Person-row via a subquery so that
    e.g. authors:"john doe" finds a Person with given=john AND family=doe.
    """
    tokens = value.split()
    q = Q()
    for token in tokens:
        q |= Q(authors__given_name__icontains=token)
        q |= Q(authors__family_name__icontains=token)

    if len(tokens) >= 2:
        # Same-row match: first token ~ given_name, last token ~ family_name
        matching_persons = Person.objects.filter(
            given_name__icontains=tokens[0],
            family_name__icontains=tokens[-1],
        )
        q |= Q(authors__in=matching_persons)

    return q


def build_field_query(query: str, tokens: list[str], fields: list[str]) -> Q:
    """Build a case-insensitive OR query across fields for a query and tokens."""
    q = Q()
    for field in fields:
        if query:
            q |= Q(**{f"{field}__icontains": query})
        for token in tokens:
            q |= Q(**{f"{field}__icontains": token})
    return q


def serialize_results(result_ids: list[str], mode: str, request: HttpRequest) -> JsonResponse:
    if mode == "id":
        return JsonResponse({"results": result_ids})
    software_map = {
        str(s.id): s
        for s in Software.objects.filter(id__in=result_ids)
    }
    jsonld_list = []
    for uid in result_ids:
        s = software_map.get(uid)
        if s:
            serializer = SoftwareSerializer(s, context={"request": request})
            serializer._view = SerialView.JSONLD
            jsonld_list.append(serializer.data)
    return JsonResponse({"results": jsonld_list})


def search_visible_software(request: HttpRequest) -> JsonResponse:
    """
    Search visible software by query terms and return ordered result IDs.

    Supports field:"value" syntax for targeted field filtering. Field filters
    are applied as exclusive AND conditions before tier ranking. Any remaining
    plain text uses the standard tiered search within the filtered set.
    """
    start_time = time.monotonic()
    raw_query = (request.GET.get("q") or "").strip()
    mode = (request.GET.get("mode") or "jsonld").lower()
    if mode not in ("id", "jsonld"):
        return JsonResponse({"error": f"Invalid mode '{mode}'. Must be 'id' or 'jsonld'."}, status=400)
    if not raw_query:
        return JsonResponse({"results": []})

    field_queries, remainder = parse_field_queries(raw_query)
    print(f"[search] raw='{raw_query}' fields={field_queries} remainder='{remainder}'")

    visible_ids = list(VerifiedSoftware.objects.values_list("id", flat=True))
    base_qs = Software.objects.filter(id__in=visible_ids)

    # Apply field filters as exclusive AND conditions, narrowing the base queryset
    if field_queries:
        field_filter = Q()
        unknown_tokens: list[str] = []

        # Collect values per alias so multiple author:"x" author:"y" tokens OR together
        alias_groups: dict[str, list[str]] = {}
        for alias, value in field_queries:
            if value:
                alias_groups.setdefault(alias, []).append(value)

        for alias, values in alias_groups.items():
            lookups = _FIELD_ALIAS_MAP.get(alias)
            if lookups is None and alias in _FIELD_ALIAS_MAP:
                # Author special case: OR across all provided values
                author_q = Q()
                for v in values:
                    author_q |= build_author_query(v)
                field_filter &= author_q
            elif lookups is not None:
                # Regular field: OR across values, then AND this alias into the filter
                alias_q = Q()
                for v in values:
                    value_q = Q()
                    for lookup in lookups:
                        value_q |= Q(**{lookup: v})
                    alias_q |= value_q
                field_filter &= alias_q
            else:
                # Unknown alias — pass the token through as plain text
                for v in values:
                    unknown_tokens.append(f'{alias}:"{v}"')

        base_qs = base_qs.filter(field_filter).distinct()
        if unknown_tokens:
            remainder = (remainder + " " + " ".join(unknown_tokens)).strip()

    query = remainder
    if not query:
        # Pure field-filter query with no remainder text — return ordered flat results
        result_ids = [str(uid) for uid in base_qs.values_list("id", flat=True)]
        total_elapsed = time.monotonic() - start_time
        print(f"[search] field-only total_results={len(result_ids)} elapsed={total_elapsed:.3f}s")
        return serialize_results(result_ids, mode, request)

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
        ],
    ]

    def fetch_tier_ids(tier_name: str, fields: list[str]) -> list[str]:
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
            if uid not in seen:
                seen.add(uid)
                result_ids.append(uid)

    total_elapsed = time.monotonic() - start_time
    print(f"[search] total_results={len(result_ids)} elapsed={total_elapsed:.3f}s")
    return serialize_results(result_ids, mode, request)
