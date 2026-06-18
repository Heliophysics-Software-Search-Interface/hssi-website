"""Tests for the ``check_software_versions`` management command.

Covers the ported version-comparison logic, GitHub release parsing (with the
network mocked), and the command end-to-end asserting that the default run is
detection-only (no DB writes) while ``--apply`` records new versions.
"""

from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from website.models import Software, SoftwareVersion
from website.management.commands import check_software_versions as cmd


def make_response(json_data, ok=True):
	"""Build a stand-in for a ``requests`` Response."""
	response = mock.Mock()
	response.json.return_value = json_data
	if ok:
		response.raise_for_status.return_value = None
	else:
		response.raise_for_status.side_effect = Exception("HTTP error")
	return response


class VersionCompareTests(SimpleTestCase):
	def test_parse_version_handles_clean_pep440(self):
		self.assertEqual(cmd.parse_version("v1.2.3"), cmd.Version("1.2.3"))
		self.assertEqual(cmd.parse_version("0.7.0"), cmd.Version("0.7.0"))
		# A PEP 440 pre-release is recognised as such.
		self.assertTrue(cmd.parse_version("0.2b1").is_prerelease)

	def test_parse_version_coerces_non_pep440_tags(self):
		# Repo-name prefixes and odd suffixes are not PEP 440; digit runs are used.
		self.assertEqual(cmd.parse_version("MAGE_1.25.1"), cmd.Version("1.25.1"))
		self.assertEqual(cmd.parse_version("kaipy-1.1.4"), cmd.Version("1.1.4"))
		self.assertEqual(cmd.parse_version("TIEGCM-3.0.1"), cmd.Version("3.0.1"))
		self.assertEqual(cmd.parse_version("v0.30.1fix"), cmd.Version("0.30.1"))
		self.assertEqual(cmd.parse_version("VAPOR3_1_0_RC0"), cmd.Version("3.1.0.0"))

	def test_parse_version_returns_none_without_digits(self):
		self.assertIsNone(cmd.parse_version("Weekly"))
		self.assertIsNone(cmd.parse_version(""))

	def test_is_newer_true_for_higher(self):
		self.assertTrue(cmd.is_newer("v2.0.0", "v1.0.0"))
		self.assertTrue(cmd.is_newer("1.1.1", "1.1"))
		self.assertTrue(cmd.is_newer("v1.2.0", "v1.1.9"))

	def test_is_newer_false_for_equal(self):
		# v1.1 and 1.1.0 are the same version under PEP 440, so not "newer".
		self.assertFalse(cmd.is_newer("v1.1", "1.1.0"))
		self.assertFalse(cmd.is_newer("1.0.0", "1.0.0"))

	def test_is_newer_false_for_downgrade(self):
		# The crux of the fix: an older release must not be reported as an update.
		self.assertFalse(cmd.is_newer("v7.1.1", "v7.1.2"))
		self.assertFalse(cmd.is_newer("v1.0", "v2.4.0"))
		self.assertFalse(cmd.is_newer("v0.6.0", "v1.0"))

	def test_is_newer_prerelease_ordering(self):
		# A real release outranks an older beta of a lower line; a beta does not
		# outrank the stable release of the same line.
		self.assertTrue(cmd.is_newer("0.7.0", "0.6.0"))
		self.assertFalse(cmd.is_newer("0.2b1", "0.6.0"))
		self.assertFalse(cmd.is_newer("1.0.0b1", "1.0.0"))

	def test_is_newer_against_empty_or_unparseable_current(self):
		self.assertTrue(cmd.is_newer("v1.0.0", ""))
		self.assertTrue(cmd.is_newer("v1.0.0", "Weekly"))

	def test_is_newer_false_when_candidate_unparseable(self):
		self.assertFalse(cmd.is_newer("nightly", "1.0.0"))


class ParseOwnerRepoTests(SimpleTestCase):
	def test_basic(self):
		self.assertEqual(
			cmd.parse_owner_repo("https://github.com/owner/repo"),
			("owner", "repo"),
		)

	def test_trailing_path_and_git_suffix(self):
		self.assertEqual(
			cmd.parse_owner_repo("https://github.com/owner/repo.git"),
			("owner", "repo"),
		)
		self.assertEqual(
			cmd.parse_owner_repo("https://github.com/owner/repo/tree/main"),
			("owner", "repo"),
		)

	def test_non_github(self):
		self.assertIsNone(cmd.parse_owner_repo("https://gitlab.com/owner/repo"))

	def test_incomplete(self):
		self.assertIsNone(cmd.parse_owner_repo("https://github.com/owner"))
		self.assertIsNone(cmd.parse_owner_repo(""))


class ReleaseParsingTests(SimpleTestCase):
	def test_parses_tag_notes_and_date_from_session(self):
		payload = [{
			"html_url": "https://github.com/owner/repo/releases/tag/v3.2.1",
			"body": "Release notes here",
			"published_at": "2024-05-06T12:00:00Z",
		}]
		session = mock.Mock()
		session.get.return_value = make_response(payload)

		release = cmd.fetch_latest_release(session, "owner", "repo", token=None)

		self.assertEqual(release.tag, "v3.2.1")
		self.assertEqual(release.notes, "Release notes here")
		self.assertEqual(release.release_date().isoformat(), "2024-05-06")

	def test_picks_highest_version_not_most_recently_published(self):
		# GitHub lists releases newest-published first; a back-ported patch to an
		# older line (v7.1.1) can appear before the higher v7.1.2. We must pick the
		# highest version, not releases[0].
		payload = [
			{
				"html_url": "https://github.com/owner/repo/releases/tag/v7.1.1",
				"body": "patch",
				"published_at": "2026-04-29T00:00:00Z",
			},
			{
				"html_url": "https://github.com/owner/repo/releases/tag/v7.1.2",
				"body": "minor",
				"published_at": "2026-03-01T00:00:00Z",
			},
		]
		session = mock.Mock()
		session.get.return_value = make_response(payload)

		release = cmd.fetch_latest_release(session, "owner", "repo", token=None)
		self.assertEqual(release.tag, "v7.1.2")

	def test_skips_draft_releases(self):
		payload = [
			{
				"html_url": "https://github.com/owner/repo/releases/tag/v9.9.9",
				"body": "draft",
				"published_at": "2026-01-01T00:00:00Z",
				"draft": True,
			},
			{
				"html_url": "https://github.com/owner/repo/releases/tag/v2.0.0",
				"body": "real",
				"published_at": "2025-01-01T00:00:00Z",
			},
		]
		session = mock.Mock()
		session.get.return_value = make_response(payload)

		release = cmd.fetch_latest_release(session, "owner", "repo", token=None)
		self.assertEqual(release.tag, "v2.0.0")

	def test_prefers_full_release_over_higher_prerelease(self):
		# A pre-release that parses to a higher tuple must not win over a real
		# release (mirrors OCBpy's old 0.2b1 beta vs the real 0.7.0).
		payload = [
			{
				"html_url": "https://github.com/owner/repo/releases/tag/0.2b1",
				"body": "beta",
				"published_at": "2018-04-12T00:00:00Z",
				"prerelease": True,
			},
			{
				"html_url": "https://github.com/owner/repo/releases/tag/0.7.0",
				"body": "stable",
				"published_at": "2026-06-05T00:00:00Z",
				"prerelease": False,
			},
		]
		session = mock.Mock()
		session.get.return_value = make_response(payload)

		release = cmd.fetch_latest_release(session, "owner", "repo", token=None)
		self.assertEqual(release.tag, "0.7.0")

	def test_falls_back_to_prerelease_when_no_full_release(self):
		payload = [
			{
				"html_url": "https://github.com/owner/repo/releases/tag/v1.0.0rc1",
				"body": "rc",
				"published_at": "2026-01-01T00:00:00Z",
				"prerelease": True,
			},
		]
		session = mock.Mock()
		session.get.return_value = make_response(payload)

		release = cmd.fetch_latest_release(session, "owner", "repo", token=None)
		self.assertEqual(release.tag, "v1.0.0rc1")

	def test_no_releases_returns_none(self):
		session = mock.Mock()
		session.get.return_value = make_response([])
		self.assertIsNone(
			cmd.fetch_latest_release(session, "owner", "repo", token=None)
		)

	def test_token_sets_auth_header(self):
		session = mock.Mock()
		session.get.return_value = make_response([])
		cmd.fetch_latest_release(session, "owner", "repo", token="secret")
		_, kwargs = session.get.call_args
		self.assertEqual(kwargs["headers"]["Authorization"], "Bearer secret")

	def test_release_date_handles_missing(self):
		info = cmd.ReleaseInfo(tag="v1", notes="", published_at=None)
		self.assertIsNone(info.release_date())


class CurrentVersionTests(TestCase):
	def test_no_versions_returns_empty(self):
		software = Software.objects.create(software_name="NoVer")
		self.assertEqual(cmd.current_version_number(software), "")

	def test_prefers_latest_release_date(self):
		software = Software.objects.create(software_name="Dated")
		old = SoftwareVersion.objects.create(number="1.0.0", release_date="2020-01-01")
		new = SoftwareVersion.objects.create(number="2.0.0", release_date="2023-01-01")
		software.version.set([old, new])
		self.assertEqual(cmd.current_version_number(software), "2.0.0")


class CheckCommandTests(TestCase):
	"""End-to-end command behavior with GitHub mocked."""

	def setUp(self):
		self.software = Software.objects.create(
			software_name="Widget",
			code_repository_url="https://github.com/acme/widget",
		)
		version = SoftwareVersion.objects.create(number="1.0.0")
		self.software.version.set([version])

	def _release(self, tag="v2.0.0"):
		return cmd.ReleaseInfo(
			tag=tag,
			notes="Big update",
			published_at="2024-01-02T00:00:00Z",
		)

	def test_detect_only_makes_no_writes(self):
		out = StringIO()
		before = SoftwareVersion.objects.count()
		with mock.patch.object(
			cmd, "fetch_latest_release", return_value=self._release("v2.0.0")
		):
			call_command("check_software_versions", stdout=out)

		self.assertEqual(SoftwareVersion.objects.count(), before)
		self.assertEqual(cmd.current_version_number(self.software), "1.0.0")
		output = out.getvalue()
		self.assertIn("Widget", output)
		self.assertIn("1.0.0 -> v2.0.0", output)
		self.assertIn("Detection only", output)

	def test_up_to_date_not_reported(self):
		out = StringIO()
		with mock.patch.object(
			cmd, "fetch_latest_release", return_value=self._release("1.0.0")
		):
			call_command("check_software_versions", stdout=out)
		self.assertIn("No out-of-date software found", out.getvalue())

	def test_downgrade_not_flagged(self):
		# Current recorded version is higher than the (mocked) latest release.
		out = StringIO()
		with mock.patch.object(
			cmd, "fetch_latest_release", return_value=self._release("v0.9.0")
		):
			call_command("check_software_versions", stdout=out)
		output = out.getvalue()
		self.assertIn("No out-of-date software found", output)
		self.assertIn("1 up-to-date", output)

	def test_missing_version_is_flagged(self):
		# Every software should have a version; one with none recorded is flagged
		# even though there is nothing to compare against.
		no_version = Software.objects.create(
			software_name="Versionless",
			code_repository_url="https://github.com/acme/versionless",
		)
		out = StringIO()
		# self.software is at 1.0.0, mock returns 1.0.0 -> only the versionless one
		# should be reported as out-of-date.
		with mock.patch.object(
			cmd, "fetch_latest_release", return_value=self._release("v1.0.0")
		):
			call_command("check_software_versions", stdout=out)
		output = out.getvalue()
		self.assertIn("Versionless", output)
		self.assertIn("no version recorded", output)
		self.assertIn("1 out-of-date (1 with no version recorded)", output)
		# Detection only: the versionless software still has no version.
		no_version.refresh_from_db()
		self.assertEqual(cmd.current_version_number(no_version), "")

	def test_apply_creates_new_version(self):
		out = StringIO()
		with mock.patch.object(
			cmd, "fetch_latest_release", return_value=self._release("v2.0.0")
		):
			call_command("check_software_versions", "--apply", stdout=out)

		self.software.refresh_from_db()
		self.assertEqual(cmd.current_version_number(self.software), "v2.0.0")
		new_version = self.software.version.get()
		self.assertEqual(new_version.number, "v2.0.0")
		self.assertEqual(new_version.release_date.isoformat(), "2024-01-02")
		self.assertEqual(new_version.description, "Big update")
		self.assertIn("Applied 1 update", out.getvalue())

	def test_errors_collected_not_raised(self):
		out = StringIO()
		with mock.patch.object(
			cmd, "fetch_latest_release", side_effect=Exception("boom")
		):
			call_command("check_software_versions", stdout=out)
		output = out.getvalue()
		self.assertIn("1 errors", output)
		self.assertIn("Widget", output)

	def test_http_error_is_concise_and_flags_rate_limit(self):
		out = StringIO()
		response = mock.Mock()
		response.status_code = 429
		http_error = cmd.requests.exceptions.HTTPError("429 too many requests")
		http_error.response = response
		with mock.patch.object(
			cmd, "fetch_latest_release", side_effect=http_error
		):
			call_command("check_software_versions", stdout=out)
		output = out.getvalue()
		self.assertIn("HTTP 429", output)
		self.assertIn("GitHub rate limit hit", output)
		# Concise: no Python traceback noise for expected HTTP errors.
		self.assertNotIn("Traceback (most recent call last)", output)

	def test_limit_caps_candidates(self):
		Software.objects.create(
			software_name="Gadget",
			code_repository_url="https://github.com/acme/gadget",
		)
		out = StringIO()
		with mock.patch.object(
			cmd, "fetch_latest_release", return_value=self._release()
		) as fetch:
			call_command("check_software_versions", "--limit", "1", stdout=out)
		self.assertEqual(fetch.call_count, 1)
