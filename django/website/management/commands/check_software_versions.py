import re

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from packaging.version import InvalidVersion, Version

from website import github
from website.models import Software, VerifiedSoftware

LABEL = "new version"

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

def issue_body(software: Software, release: dict, listed: str) -> str:
	page = f"{settings.SITE_PROTOCOL}://{settings.SITE_DOMAIN}{software.get_absolute_url()}"
	return (
		f"[{software.software_name}]({page}) has a new version on GitHub: "
		f"[{release['tag_name']}]({release['html_url']}). HSSI lists {listed}.\n\n"
		"Run the HSSI Metadata Updater agent on it to bring its HSSI metadata up to date."
	)

class Command(BaseCommand):
	help = "List visible software with a newer version on GitHub than the version HSSI lists."

	def add_arguments(self, parser):
		parser.add_argument(
			"--open-issues",
			action="store_true",
			help=f'Open a "{LABEL}" GitHub issue for each new version without one, closing the issues it supersedes.',
		)

	def handle(self, *args, open_issues: bool, **options):
		if not settings.HSSI_GITHUB_TOKEN:
			raise CommandError("Set HSSI_GITHUB_TOKEN to read GitHub releases.")
		issues = github.issues() if open_issues else []
		titles = {issue["title"] for issue in issues}
		software_list = Software.objects.filter(
			pk__in=VerifiedSoftware.objects.values("id"),
			code_repository_url__icontains="github.com",
		)

		newer = 0
		for software in software_list:
			try:
				release = github.latest_release(software.code_repository_url)
			except requests.RequestException as error:
				self.stderr.write(f"{software.software_name}: {error}")
				continue
			version = software.latest_version()
			current = version.number if version else ""
			if not release or not is_newer(release["tag_name"], current):
				continue
			newer += 1
			listed = f"version {current}" if current else "no version"
			prefix = f"New version of {software.software_name}: "
			title = prefix + release["tag_name"]
			self.stdout.write(f"{title} (HSSI lists {listed})")
			if not open_issues or title in titles:
				continue
			opened = github.open_issue(title, issue_body(software, release, listed), LABEL)
			titles.add(title)
			for issue in issues:
				if issue["state"] == "open" and issue["title"].startswith(prefix):
					github.close_issue(issue["number"], f"Superseded by #{opened['number']}.")
		self.stdout.write(f"{newer} of {len(software_list)} GitHub-hosted visible software have a newer version.")
