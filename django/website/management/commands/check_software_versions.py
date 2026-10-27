import re, time
from typing import NamedTuple
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from packaging.version import InvalidVersion, Version

from website import github
from website.models import Software, VerifiedSoftware

LABEL = "new version"
TIMEOUT = 15

# Software whose versions appear on a web page that the other sources don't read,
# by HSSI name: the page, and a pattern matching each version on it.
PAGES = {
	"AMGeO": ("https://ccmc.gsfc.nasa.gov/models/AMGeO~3/", r"Version (\d[\d.]*) was deployed"),
	"Autoplot": ("https://autoplot.org/latest/", r"Autoplot Application \((v\w+)\)"),
	"IGRF-14": ("https://zenodo.org/records/14012302/latest", r"\| Version (v\d+)"),
	"SPEDAS (Space Physics Environment Data Analysis System)": ("https://spedas.org/downloads/", r"spedas_(\d+_\d+)\.zip"),
}

class Release(NamedTuple):
	version: str
	url: str

class PageChanged(Exception):
	"""A page in PAGES no longer shows a version its pattern matches."""

def parse_version(tag: str) -> Version | None:
	"""Parse a version, falling back to its digit runs for tags like "MAGE_1.25.1"."""
	for candidate in (tag, ".".join(re.findall(r"\d+", tag))):
		try:
			return Version(candidate)
		except InvalidVersion:
			pass
	return None

def is_newer(tag: str, current: str) -> bool:
	"""Whether the tag is a higher version than current, which may be empty or unparseable."""
	new, old = parse_version(tag), parse_version(current)
	return new is not None and (old is None or new > old)

def is_stable(version: str) -> bool:
	"""Whether the version parses and isn't a prerelease, including ones like "VAPOR3_1_0_RC0"."""
	parsed = parse_version(version)
	return parsed is not None and not parsed.is_prerelease and not re.search(r"(?i)\d.*(rc|alpha|beta|pre|dev)", version)

def github_release(software: Software) -> Release | None:
	"""The highest stable GitHub release, which GitHub may not mark Latest."""
	urls = {
		release["tag_name"]: release["html_url"]
		for release in github.releases(software.code_repository_url or "")
		if not release["draft"] and not release["prerelease"] and is_stable(release["tag_name"])
	}
	tag = max(urls, key=parse_version, default=None)
	return Release(tag, urls[tag]) if tag else None

def pypi_release(software: Software) -> Release | None:
	"""The highest stable release of a PyPI project named like the software or its repository,
	if the project links that repository or has published the version HSSI lists."""
	repo = github.repo_path(software.code_repository_url or "") or ""
	version = software.latest_version()
	listed = parse_version(version.number) if version else None
	names = {re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") for name in (software.software_name, repo.partition("/")[2])}
	for name in sorted(names - {""}):
		response = requests.get(f"https://pypi.org/pypi/{name}/json", timeout=TIMEOUT)
		if response.status_code == 404:
			continue
		response.raise_for_status()
		project = response.json()
		versions = [number for number, files in project["releases"].items() if files]
		info = project["info"]
		links = " ".join(filter(None, [info.get("home_page"), *(info.get("project_urls") or {}).values()])).lower()
		if (repo and repo.lower() in links) or (listed and listed in map(parse_version, versions)):
			newest = max(filter(is_stable, versions), key=parse_version, default=None)
			return Release(newest, f"https://pypi.org/project/{name}/{newest}/") if newest else None
	return None

def zenodo_release(software: Software) -> Release | None:
	"""The version of the newest record in the Zenodo version family of the software's DOI."""
	match = re.search(r"zenodo\.(\d+)", software.persistent_identifier or "")
	if not match:
		return None
	time.sleep(1)  # Zenodo allows 133 requests a minute, and each lookup makes two
	response = requests.get(f"https://zenodo.org/api/records/{match[1]}/versions/latest", timeout=TIMEOUT)
	response.raise_for_status()
	record = response.json()
	version = record["metadata"].get("version") or ""
	return Release(version, record["links"]["self_html"]) if is_stable(version) else None

def page_release(software: Software) -> Release | None:
	"""The highest version on the software's page in PAGES."""
	if software.software_name not in PAGES:
		return None
	url, pattern = PAGES[software.software_name]
	response = requests.get(url, timeout=TIMEOUT)
	if response.status_code == 429 or response.status_code >= 500:
		response.raise_for_status()
	versions = [match for match in re.findall(pattern, response.text) if parse_version(match)]
	if not versions:
		raise PageChanged(f"{url} answered {response.status_code} with no version matching `{pattern}`.")
	return Release(max(versions, key=parse_version), url)

SOURCES = (github_release, pypi_release, zenodo_release, page_release)

def issue_body(software: Software, release: Release, listed: str) -> str:
	page = f"{settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}{software.get_absolute_url()}"
	return (
		f"[{software.software_name}]({page}) has a new version on {urlparse(release.url).netloc}: "
		f"[{release.version}]({release.url}). HSSI lists {listed}.\n\n"
		"Run the HSSI Metadata Updater agent on it to bring its HSSI metadata up to date."
	)

class Command(BaseCommand):
	help = "List visible software with a newer version on GitHub, PyPI, Zenodo, or its page in PAGES than the version HSSI lists."

	def add_arguments(self, parser):
		parser.add_argument(
			"--open-issues",
			action="store_true",
			help=f'Open a "{LABEL}" GitHub issue for each new version without one, closing the issues it supersedes, '
			'and a "bug" issue for each entry in PAGES that stops working.',
		)

	def handle(self, *args, open_issues: bool, **options):
		if not settings.HSSI_GITHUB_TOKEN:
			raise CommandError("Set HSSI_GITHUB_TOKEN to read GitHub releases.")
		self.issues = github.issues() if open_issues else None
		software_list = Software.objects.filter(pk__in=VerifiedSoftware.objects.values("id"))

		newer = 0
		for software in software_list:
			release = self.newest_release(software)
			version = software.latest_version()
			current = version.number if version else ""
			if not release or not is_newer(release.version, current):
				continue
			newer += 1
			listed = f"version {current}" if current else "no version"
			self.stdout.write(f"New version of {software.software_name}: {release.version} (HSSI lists {listed})")
			if self.issues is not None:
				self.open_version_issue(software, release, listed)
		for name in PAGES.keys() - {software.software_name for software in software_list}:
			self.report_broken_page(name, PageChanged("No visible software has this name."))
		self.stdout.write(f"{newer} of {len(software_list)} visible software have a newer version.")

	def newest_release(self, software: Software) -> Release | None:
		"""The highest release any source finds, reporting each source that fails."""
		releases = []
		for source in SOURCES:
			try:
				releases.append(source(software))
			except PageChanged as error:
				self.report_broken_page(software.software_name, error)
			except Exception as error:
				self.stderr.write(f"{software.software_name}: {error}")
		return max(filter(None, releases), key=lambda release: parse_version(release.version), default=None)

	def open_version_issue(self, software: Software, release: Release, listed: str) -> None:
		"""Open an issue for the release unless one exists for it or a higher version,
		then close the open issues for lower versions."""
		prefix = f"New version of {software.software_name}: "
		def version(issue: dict) -> Version:
			return parse_version(issue["title"].removeprefix(prefix)) or Version("0")
		reported = [issue for issue in self.issues if issue["title"].startswith(prefix)]
		newest = max(reported, key=version, default=None)
		if not newest or version(newest) < parse_version(release.version):
			newest = github.open_issue(prefix + release.version, issue_body(software, release, listed), LABEL)
			self.issues.append(newest)
		for issue in reported:
			if issue["state"] == "open" and version(issue) < version(newest):
				github.close_issue(issue["number"], f"Superseded by #{newest['number']}.")
				issue["state"] = "closed"

	def report_broken_page(self, name: str, error: PageChanged) -> None:
		"""Print why a PAGES entry failed and, with --open-issues, open a "bug" issue for it unless one is open."""
		self.stderr.write(f"{name}: {error}")
		title = f"Can't read the version of {name}"
		if self.issues is None or any(issue["state"] == "open" and issue["title"] == title for issue in self.issues):
			return
		body = (
			f"The version check couldn't read {name}'s version: {error}\n\n"
			"Update its entry in `PAGES` in `django/website/management/commands/check_software_versions.py`."
		)
		self.issues.append(github.open_issue(title, body, "bug"))
