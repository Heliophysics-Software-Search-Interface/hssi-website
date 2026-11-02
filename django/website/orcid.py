"""Read the public name on an ORCID record."""

import re

import requests

API = "https://pub.orcid.org/v3.0"
ORCID_URL = re.compile(r"https://orcid\.org/(\d{4}-\d{4}-\d{4}-\d{3}[\dX])")
TIMEOUT = 5

def public_name(identifier: str | None) -> tuple[str, str] | None:
	"""The given and family names on the ORCID record that ``identifier``, an
	ORCID iD URL, names. None if it isn't one, or the record shows no name or
	can't be read."""
	match = ORCID_URL.fullmatch(identifier or "")
	if not match:
		return None
	try:
		response = requests.get(
			f"{API}/{match[1]}/personal-details",
			headers={"Accept": "application/json"},
			timeout=TIMEOUT,
		)
		response.raise_for_status()
		name = response.json().get("name") or {}
	except requests.RequestException:
		return None
	given = (name.get("given-names") or {}).get("value") or ""
	family = (name.get("family-name") or {}).get("value") or ""
	return (given, family) if given or family else None
