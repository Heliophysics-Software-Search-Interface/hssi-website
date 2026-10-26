"""Read GitHub releases and manage issues in the hssi-website repository."""

import itertools, re

import requests
from django.conf import settings

API = "https://api.github.com"
ISSUES = f"{API}/repos/Heliophysics-Software-Search-Interface/hssi-website/issues"
REPO_PATH = re.compile(r"github\.com/([^/]+)/([^/?#]+)", re.IGNORECASE)
TIMEOUT = 5

def _headers() -> dict[str, str]:
	return {
		"Accept": "application/vnd.github+json",
		"Authorization": f"Bearer {settings.HSSI_GITHUB_TOKEN}",
	}

def latest_release(repo_url: str) -> dict | None:
	"""The release GitHub marks Latest for a github.com repository, or None."""
	match = REPO_PATH.search(repo_url)
	if not match:
		return None
	repo = f"{match[1]}/{match[2].removesuffix('.git')}"
	response = requests.get(f"{API}/repos/{repo}/releases/latest", headers=_headers(), timeout=TIMEOUT)
	if response.status_code == 404:
		return None
	response.raise_for_status()
	return response.json()

def issues() -> list[dict]:
	"""Every issue in the repository, open or closed."""
	found: list[dict] = []
	for page in itertools.count(1):
		response = requests.get(
			ISSUES,
			headers=_headers(),
			params={"state": "all", "per_page": 100, "page": page},
			timeout=TIMEOUT,
		)
		response.raise_for_status()
		found += response.json()
		if "next" not in response.links:
			return found

def open_issue(title: str, body: str, label: str) -> dict:
	response = requests.post(
		ISSUES,
		headers=_headers(),
		json={"title": title, "body": body, "labels": [label]},
		timeout=TIMEOUT,
	)
	response.raise_for_status()
	return response.json()

def close_issue(number: int, comment: str) -> None:
	"""Comment on an issue, then close it as not planned."""
	response = requests.post(
		f"{ISSUES}/{number}/comments",
		headers=_headers(),
		json={"body": comment},
		timeout=TIMEOUT,
	)
	response.raise_for_status()
	response = requests.patch(
		f"{ISSUES}/{number}",
		headers=_headers(),
		json={"state": "closed", "state_reason": "not_planned"},
		timeout=TIMEOUT,
	)
	response.raise_for_status()
