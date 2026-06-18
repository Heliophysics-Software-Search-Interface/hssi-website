"""Detect (and optionally apply) new GitHub releases for HSSI software.

Ported in spirit from EMAC's ``git_fetch_version`` view, but reworked for HSSI:

* Reads software directly via the ORM (no HTTP API needed).
* **Defaults to detection only** — it reports which GitHub-hosted software have a
  newer release than what HSSI currently records, and writes nothing.
* ``--apply`` (opt-in) creates a new ``SoftwareVersion`` for each out-of-date entry
  and points the software at it. This is intentionally off by default.

Usage examples (run from the ``django`` directory or inside the app container)::

    python manage.py check_software_versions
    python manage.py check_software_versions --csv /tmp/outdated.csv
    python manage.py check_software_versions --limit 5
    python manage.py check_software_versions --apply        # opt-in: writes to the DB

A GitHub token may be supplied with ``--github-token`` or the ``GITHUB_TOKEN``
environment variable to raise the API rate limit (anonymous is 60 requests/hour).
"""

from __future__ import annotations

import csv as csv_module
import datetime
import os
import re
import traceback
from dataclasses import dataclass, field

import requests
from django.core.management.base import BaseCommand, CommandError

from website.models import Software, SoftwareVersion


GITHUB_API = "https://api.github.com"


def version_tuple(version: str) -> tuple[int, ...]:
	"""Extract a comparable numeric tuple from a version/tag string.

	Strips everything except digits and dots — so ``v1.2``, ``kaipy-1.1.4`` and
	``TIEGCM-3.0.1`` reduce to their numeric components — then splits on dots.
	Returns an empty tuple when there is no numeric component.
	"""
	cleaned = re.sub(r"[^\d\.]", "", version or "").strip(".")
	parts: list[int] = []
	for chunk in cleaned.split("."):
		if chunk == "":
			continue
		try:
			parts.append(int(chunk))
		except ValueError:
			pass
	return tuple(parts)


def is_newer(candidate: str, current: str) -> bool:
	"""Return True if ``candidate`` is a strictly higher version than ``current``.

	Zero-pads the shorter tuple so e.g. ``v1.1`` and ``1.1.0`` compare equal (and
	are therefore *not* newer), while ``1.1.1`` is newer than ``1.1``. This is what
	prevents an older release that happens to be published more recently (a
	*downgrade*, e.g. a back-ported patch) from being reported as an update.
	"""
	cand = version_tuple(candidate)
	cur = version_tuple(current)
	length = max(len(cand), len(cur))
	cand += (0,) * (length - len(cand))
	cur += (0,) * (length - len(cur))
	return cand > cur


def parse_owner_repo(repo_url: str) -> tuple[str, str] | None:
	"""Extract ``(owner, repo)`` from a github.com URL, or None if not parseable."""
	if not repo_url or "github.com" not in repo_url:
		return None
	try:
		after = repo_url.split("github.com/", 1)[1]
	except IndexError:
		return None
	parts = [p for p in after.strip("/").split("/") if p]
	if len(parts) < 2:
		return None
	owner = parts[0]
	repo = parts[1]
	if repo.endswith(".git"):
		repo = repo[:-len(".git")]
	return owner, repo


def current_version_number(software: Software) -> str:
	"""Return the software's current recorded version number.

	Mirrors ``SoftwareSerializer._latest_version`` so detection matches what the
	site shows: prefer the version with the latest ``release_date``, otherwise the
	highest ``number`` by string sort. Empty string when no version is recorded.
	"""
	versions = list(software.version.all())
	if not versions:
		return ""
	with_dates = [v for v in versions if v.release_date]
	if with_dates:
		return max(with_dates, key=lambda v: v.release_date).number or ""
	return (sorted(versions, key=lambda v: v.number)[-1].number) or ""


@dataclass
class ReleaseInfo:
	"""The bits of a GitHub release we care about."""
	tag: str
	notes: str
	published_at: str | None

	def release_date(self) -> datetime.date | None:
		if not self.published_at:
			return None
		try:
			return datetime.datetime.strptime(
				self.published_at[:10], "%Y-%m-%d"
			).date()
		except (ValueError, TypeError):
			return None


@dataclass
class Outdated:
	"""A software entry that should adopt a newer (or any) GitHub release.

	``missing_version`` is True when HSSI has no version recorded at all — every
	software should have a version, so we flag these and suggest the latest git
	release even though there is nothing to compare against.
	"""
	software: Software
	current: str
	release: ReleaseInfo
	missing_version: bool = False


@dataclass
class CheckResult:
	outdated: list[Outdated] = field(default_factory=list)
	checked: int = 0
	up_to_date: int = 0
	no_releases: int = 0
	errors: list[str] = field(default_factory=list)
	rate_limited: bool = False


def fetch_latest_release(
	session: requests.Session,
	owner: str,
	repo: str,
	token: str | None,
) -> ReleaseInfo | None:
	"""Return the highest-version release for ``owner/repo``, or None if none exist.

	GitHub returns the releases list ordered by publish date, so the first entry is
	not necessarily the highest version (a back-ported patch to an older line can be
	published after a newer release). We therefore pick the release with the highest
	numeric version among all non-draft releases, so the caller compares against the
	true latest version rather than merely the most recently published one.

	Raises ``requests.HTTPError`` (via ``raise_for_status``) on a non-2xx response
	so the caller can record the failure per-software without aborting the run.
	"""
	url = f"{GITHUB_API}/repos/{owner}/{repo}/releases"
	headers = {
		"Accept": "application/vnd.github+json",
		"User-Agent": "HSSI-version-checker",
	}
	if token:
		headers["Authorization"] = f"Bearer {token}"
	response = session.get(
		url, headers=headers, params={"per_page": 100}, timeout=30
	)
	response.raise_for_status()
	releases = response.json()
	if not releases:
		return None

	best = None
	best_tag = ""
	best_tuple: tuple[int, ...] | None = None
	for rel in releases:
		if rel.get("draft"):
			continue
		html_url = rel.get("html_url") or ""
		# Tag taken from the release page URL's last segment, matching EMAC.
		tag = (
			html_url.strip("/").split("/")[-1]
			if html_url
			else (rel.get("tag_name") or "")
		)
		if not tag:
			continue
		candidate_tuple = version_tuple(tag)
		if best is None or candidate_tuple > best_tuple:
			best = rel
			best_tag = tag
			best_tuple = candidate_tuple

	if best is None:
		return None
	return ReleaseInfo(
		tag=best_tag,
		notes=best.get("body") or "",
		published_at=best.get("published_at"),
	)


class Command(BaseCommand):
	help = (
		"Detect HSSI software with newer GitHub releases than recorded. "
		"Detection only by default; pass --apply to write new versions."
	)

	def add_arguments(self, parser):
		parser.add_argument(
			"--apply",
			action="store_true",
			help="Opt-in: write a new SoftwareVersion for each out-of-date entry. "
			"Off by default (detection only).",
		)
		parser.add_argument(
			"--csv",
			dest="csv_path",
			default=None,
			help="Also write the out-of-date report to this CSV file path.",
		)
		parser.add_argument(
			"--limit",
			type=int,
			default=None,
			help="Only check the first N github-hosted software (useful for testing).",
		)
		parser.add_argument(
			"--github-token",
			dest="github_token",
			default=None,
			help="GitHub token for a higher API rate limit. Falls back to the "
			"GITHUB_TOKEN environment variable.",
		)

	def handle(self, *args, **options):
		apply_changes: bool = options["apply"]
		csv_path: str | None = options["csv_path"]
		limit: int | None = options["limit"]
		token: str | None = options["github_token"] or os.environ.get("GITHUB_TOKEN")

		if limit is not None and limit < 1:
			raise CommandError("--limit must be a positive integer.")

		candidates = list(
			Software.objects.filter(
				code_repository_url__icontains="github.com"
			).order_by("software_name")
		)
		if limit is not None:
			candidates = candidates[:limit]

		if not candidates:
			self.stdout.write("No github-hosted software found to check.")
			return

		self.stdout.write(
			f"Checking {len(candidates)} github-hosted software for new releases"
			f"{' (anonymous)' if not token else ''}..."
		)

		result = self._check(candidates, token)

		self._print_report(result)
		if csv_path:
			self._write_csv(result, csv_path)

		if apply_changes:
			self._apply(result)
		elif result.outdated:
			self.stdout.write(
				"\nDetection only — no changes written. "
				"Re-run with --apply to record these new versions."
			)

	def _check(self, candidates: list[Software], token: str | None) -> CheckResult:
		result = CheckResult()
		session = requests.Session()
		for software in candidates:
			result.checked += 1
			owner_repo = parse_owner_repo(software.code_repository_url)
			if owner_repo is None:
				result.errors.append(
					f"{software.software_name}: could not parse owner/repo from "
					f"'{software.code_repository_url}'"
				)
				continue
			owner, repo = owner_repo
			try:
				release = fetch_latest_release(session, owner, repo, token)
			except requests.exceptions.RequestException as err:
				# Expected network/HTTP failures: record a concise message rather
				# than a full traceback. Flag rate limiting so we can hint at it.
				status_code = getattr(err.response, "status_code", None)
				if status_code in (403, 429):
					result.rate_limited = True
				detail = f" (HTTP {status_code})" if status_code else ""
				result.errors.append(
					f"{software.software_name}: failed to fetch releases for "
					f"{owner}/{repo}{detail}: {err}"
				)
				continue
			except Exception as err:  # noqa: BLE001 - unexpected: keep full traceback
				msg = (
					f"{software.software_name}: unexpected error for {owner}/{repo}\n"
					+ "".join(
						traceback.TracebackException.from_exception(err).format()
					)
				)
				result.errors.append(msg)
				continue

			if release is None:
				result.no_releases += 1
				continue

			current = current_version_number(software)
			if not current:
				# No version recorded in HSSI at all — flag it and suggest the
				# latest git release (every software should have a version).
				result.outdated.append(
					Outdated(
						software=software,
						current="",
						release=release,
						missing_version=True,
					)
				)
			elif is_newer(release.tag, current):
				result.outdated.append(
					Outdated(software=software, current=current, release=release)
				)
			else:
				result.up_to_date += 1
		return result

	def _print_report(self, result: CheckResult):
		self.stdout.write("")
		if result.outdated:
			self.stdout.write(self.style.WARNING("Out-of-date software:"))
			for item in result.outdated:
				current = "(no version recorded)" if item.missing_version else item.current
				date = item.release.release_date()
				date_str = date.isoformat() if date else "?"
				notes = " ".join((item.release.notes or "").split())
				if len(notes) > 80:
					notes = notes[:77] + "..."
				self.stdout.write(
					f"  - {item.software.software_name}: "
					f"{current} -> {item.release.tag} "
					f"(released {date_str})"
				)
				self.stdout.write(f"      repo:  {item.software.code_repository_url}")
				self.stdout.write(f"      uuid:  {item.software.id}")
				if notes:
					self.stdout.write(f"      notes: {notes}")
		else:
			self.stdout.write(self.style.SUCCESS("No out-of-date software found."))

		self.stdout.write("")
		missing = sum(1 for item in result.outdated if item.missing_version)
		self.stdout.write(
			"Summary: "
			f"{result.checked} checked, "
			f"{len(result.outdated)} out-of-date "
			f"({missing} with no version recorded), "
			f"{result.up_to_date} up-to-date, "
			f"{result.no_releases} with no releases, "
			f"{len(result.errors)} errors."
		)
		if result.errors:
			self.stdout.write(self.style.ERROR("\nErrors:"))
			for err in result.errors:
				self.stdout.write(f"  - {err}")
		if result.rate_limited:
			self.stdout.write(self.style.WARNING(
				"\nGitHub rate limit hit (HTTP 403/429). Supply a token via "
				"--github-token or the GITHUB_TOKEN environment variable "
				"(anonymous requests are limited to 60/hour)."
			))

	def _write_csv(self, result: CheckResult, csv_path: str):
		with open(csv_path, "w", newline="", encoding="utf-8") as handle:
			writer = csv_module.writer(handle)
			writer.writerow([
				"software_name",
				"current_version",
				"latest_version",
				"release_date",
				"no_version_recorded",
				"repo_url",
				"software_uuid",
				"release_notes",
			])
			for item in result.outdated:
				date = item.release.release_date()
				notes = " ".join((item.release.notes or "").split())
				if len(notes) > 300:
					notes = notes[:297] + "..."
				writer.writerow([
					item.software.software_name,
					item.current,
					item.release.tag,
					date.isoformat() if date else "",
					"yes" if item.missing_version else "no",
					item.software.code_repository_url,
					str(item.software.id),
					notes,
				])
		self.stdout.write(f"\nWrote CSV report to {csv_path}")

	def _apply(self, result: CheckResult):
		if not result.outdated:
			self.stdout.write("\n--apply: nothing to update.")
			return
		self.stdout.write(
			self.style.WARNING(
				f"\n--apply: writing {len(result.outdated)} new version(s) to the database..."
			)
		)
		updated = 0
		for item in result.outdated:
			try:
				version_obj = SoftwareVersion.objects.create(
					number=item.release.tag,
					release_date=item.release.release_date(),
					description=item.release.notes or None,
				)
				item.software.version.set([version_obj])
				updated += 1
				self.stdout.write(
					f"  updated {item.software.software_name} -> {item.release.tag}"
				)
			except Exception as err:  # noqa: BLE001 - report, continue
				self.stdout.write(
					self.style.ERROR(
						f"  failed to update {item.software.software_name}: {err}"
					)
				)
		self.stdout.write(self.style.SUCCESS(f"Applied {updated} update(s)."))
