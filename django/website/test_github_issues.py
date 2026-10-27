import json
from io import StringIO
from unittest import mock

import requests
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings

from . import github
from .management.commands.check_software_versions import (
	LABEL, PageChanged, Release, github_release, is_newer, page_release, pypi_release, zenodo_release,
)
from .models import Software, SoftwareVersion, VerifiedSoftware

COMMAND = "website.management.commands.check_software_versions"

def make_software(name: str, version: str = "", **fields) -> Software:
	software = Software.objects.create(software_name=name, **fields)
	if version:
		software.version.add(SoftwareVersion.objects.create(number=version))
	return software

def response(status: int = 200, text: str = "", data=None) -> requests.Response:
	fake = requests.Response()
	fake.status_code = status
	fake._content = (json.dumps(data) if data is not None else text).encode()
	return fake


class IsNewerTests(SimpleTestCase):
	def test_compares_release_tags_with_the_listed_version(self):
		for tag, current, expected in (
			("v1.2.0", "1.1.9", True),
			("v1.1", "1.1.0", False),
			("7.1.1", "7.1.2", False),
			("kaipy-1.1.4", "1.1.3", True),
			("3.10.1", "Weekly", True),
			("1.0", "", True),
			("nightly", "1.0", False),
			("v2026a_8", "v2026a_6", True),
			("v2026b_1", "v2026a_8", True),
			("6_2", "6.1", True),
			("MAGE_1.5.0", "MAGE_1.25.1", True),
			("MAGE_1.25.1", "MAGE_1.5.0", False),
			("MAGE_2.0.0", "MAGE_1.75.0", True),
			("MAGE_1.5.0", "MAGE_1.5", False),
		):
			with self.subTest(tag=tag, current=current):
				self.assertEqual(is_newer(tag, current), expected)


class GitHubClientTests(SimpleTestCase):
	@mock.patch("website.github.requests.get")
	def test_reads_owner_and_repo_from_the_url(self, get):
		get.return_value = response(data=[])
		for url in (
			"https://github.com/sunpy/sunpy",
			"https://github.com/sunpy/sunpy.git",
			"https://github.com/sunpy/sunpy/tree/main",
			"https://GitHub.com/sunpy/sunpy",
		):
			with self.subTest(url=url):
				github.releases(url)
				self.assertEqual(get.call_args.args[0], "https://api.github.com/repos/sunpy/sunpy/releases")

	@mock.patch("website.github.requests.get")
	def test_repository_without_releases_has_none(self, get):
		get.return_value = response(404)
		self.assertEqual(github.releases("https://github.com/example/none"), [])
		self.assertEqual(github.releases("https://gitlab.com/example/none"), [])
		get.assert_called_once()

	@mock.patch("website.github.requests.get")
	def test_issues_follow_every_page_of_open_and_closed_issues(self, get):
		first = mock.Mock(links={"next": {"url": "page 2"}})
		first.json.return_value = [{"title": "First"}]
		last = mock.Mock(links={})
		last.json.return_value = [{"title": "Last"}]
		get.side_effect = [first, last]

		self.assertEqual(github.issues(), [{"title": "First"}, {"title": "Last"}])
		params = [call.kwargs["params"] for call in get.call_args_list]
		self.assertEqual([p["page"] for p in params], [1, 2])
		self.assertTrue(all(p["state"] == "all" for p in params))

	@mock.patch("website.github.requests.patch")
	@mock.patch("website.github.requests.post")
	def test_close_issue_comments_then_closes_as_not_planned(self, post, patch):
		github.close_issue(7, "Superseded by #9.")

		self.assertTrue(post.call_args.args[0].endswith("/issues/7/comments"))
		self.assertEqual(post.call_args.kwargs["json"], {"body": "Superseded by #9."})
		self.assertTrue(patch.call_args.args[0].endswith("/issues/7"))
		self.assertEqual(patch.call_args.kwargs["json"], {"state": "closed", "state_reason": "not_planned"})


class SourceTests(TestCase):
	@mock.patch("website.github.releases")
	def test_github_release_is_the_highest_stable_one(self, releases):
		releases.return_value = [
			{"tag_name": tag, "html_url": f"https://github.com/example/example/releases/tag/{tag}", "draft": draft, "prerelease": prerelease}
			for tag, draft, prerelease in (
				("v4.0", True, False),
				("v3.0", False, True),
				("EXAMPLE2_5_0_RC0", False, False),
				("v2.0rc1", False, False),
				("v1.5.0", False, False),
				("v1.25.1", False, False),
			)
		]
		software = make_software("Example", code_repository_url="https://github.com/example/example")
		self.assertEqual(
			github_release(software),
			Release("v1.25.1", "https://github.com/example/example/releases/tag/v1.25.1"),
		)

	@mock.patch(f"{COMMAND}.requests.get")
	def test_pypi_release_trusts_a_project_that_links_the_repository_or_lists_the_version(self, get):
		projects = {
			"space-packet-parser": {
				"info": {"home_page": None, "project_urls": {"Source": "https://github.com/medley56/space_packet_parser"}},
				"releases": {"6.1.2": ["sdist"], "6.2.0": ["sdist"], "6.3.0rc1": ["sdist"], "7.0.0": []},
			},
			"fisspy": {
				"info": {"home_page": "http://fiss.snu.ac.kr", "project_urls": None},
				"releases": {"1.3.0": ["sdist"], "1.4.5": ["sdist"]},
			},
			"pyglow": {
				"info": {"home_page": "https://github.com/spino17/PyGlow", "project_urls": None},
				"releases": {"0.1.7": ["sdist"]},
			},
			"xrtpy": {
				"info": {"home_page": None, "project_urls": {"Homepage": "https://github.com/HinodeXRT/xrtpy"}},
				"releases": {"0.5.1": ["sdist"], "0.5.2rc0": ["sdist"]},
			},
		}
		get.side_effect = lambda url, **kwargs: (
			response(data=projects[url.split("/")[4]]) if url.split("/")[4] in projects else response(404)
		)
		for name, repo, version, expected in (
			("Space Packet Parser", "medley56/space_packet_parser", "", Release("6.2.0", "https://pypi.org/project/space-packet-parser/6.2.0/")),
			("fisspy", "SNU-sunday/fisspy", "1.3.0", Release("1.4.5", "https://pypi.org/project/fisspy/1.4.5/")),
			("XRTpy: A Hinode X-Ray Telescope Python Package", "HinodeXRT/xrtpy", "", Release("0.5.1", "https://pypi.org/project/xrtpy/0.5.1/")),
			("pyglow", "timduly4/pyglow", "2.2", None),
			("Helio-KNOW", "rmcgranaghan/Helio-KNOW", "", None),
		):
			with self.subTest(name=name):
				software = make_software(name, version, code_repository_url=f"https://github.com/{repo}")
				self.assertEqual(pypi_release(software), expected)

	@mock.patch(f"{COMMAND}.time.sleep")
	@mock.patch(f"{COMMAND}.requests.get")
	def test_zenodo_release_is_the_version_of_the_newest_record(self, get, sleep):
		get.return_value = response(data={"metadata": {"version": "6.1"}, "links": {"self_html": "https://zenodo.org/records/15023025"}})
		software = make_software("SPEDAS", persistent_identifier="https://doi.org/10.5281/zenodo.14919975")
		self.assertEqual(zenodo_release(software), Release("6.1", "https://zenodo.org/records/15023025"))
		self.assertEqual(get.call_args.args[0], "https://zenodo.org/api/records/14919975/versions/latest")

		get.reset_mock()
		self.assertIsNone(zenodo_release(make_software("Unpublished")))
		get.assert_not_called()

	@mock.patch.dict(f"{COMMAND}.PAGES", {"Autoplot": ("https://autoplot.org/latest/", r"Autoplot Application \((v\w+)\)")})
	@mock.patch(f"{COMMAND}.requests.get")
	def test_page_release_reads_the_highest_version_on_the_page(self, get):
		software = make_software("Autoplot")
		get.return_value = response(text="Autoplot Application (v2026a_8) ... Autoplot Application (v2026a_10)")
		self.assertEqual(page_release(software), Release("v2026a_10", "https://autoplot.org/latest/"))

		for status, text in ((200, "<h1>A new design</h1>"), (404, "Not Found")):
			with self.subTest(status=status):
				get.return_value = response(status, text)
				with self.assertRaises(PageChanged):
					page_release(software)

		for status in (429, 503):
			with self.subTest(status=status):
				get.return_value = response(status)
				with self.assertRaises(requests.HTTPError):
					page_release(software)

		self.assertIsNone(page_release(make_software("SunPy")))


GITHUB = {
	"Stale": Release("v2.0", "https://github.com/example/stale/releases/tag/v2.0"),
	"Current": Release("v1.0", "https://github.com/example/current/releases/tag/v1.0"),
	"Hidden": Release("9.0", "https://github.com/example/hidden/releases/tag/9.0"),
	"Ahead": Release("2.0", "https://github.com/example/ahead/releases/tag/2.0"),
	"Lingering": Release("2.0", "https://github.com/example/lingering/releases/tag/2.0"),
}
PYPI = {
	"Stale": Release("2.0", "https://pypi.org/project/stale/2.0/"),
	"Known": Release("3.1", "https://pypi.org/project/known/3.1/"),
}

def fake_github(software: Software) -> Release | None:
	if software.software_name == "Broken":
		raise requests.ConnectionError("unreachable")
	return GITHUB.get(software.software_name)

def fake_pypi(software: Software) -> Release | None:
	if software.software_name == "Broken":
		raise KeyError("releases")
	return PYPI.get(software.software_name)

def fake_page(software: Software) -> Release | None:
	if software.software_name == "Paged":
		raise PageChanged("https://example.org/ answered 200 with no version matching `x`.")
	return None

ISSUES = [
	{"number": 3, "title": "New version of Stale: v1.2", "state": "closed"},
	{"number": 5, "title": "New version of Known: v3.1", "state": "closed"},
	{"number": 6, "title": "Can't read the version of Paged", "state": "closed"},
	{"number": 7, "title": "New version of Stale: v1.5", "state": "open"},
	{"number": 8, "title": "New version of Stale Fork: 1.0", "state": "open"},
	{"number": 11, "title": "New version of Ahead: 3.0", "state": "open"},
	{"number": 12, "title": "New version of Lingering: 2.0", "state": "open"},
	{"number": 13, "title": "New version of Lingering: 1.5", "state": "open"},
]


@override_settings(HSSI_GITHUB_TOKEN="token")
@mock.patch.dict(f"{COMMAND}.PAGES", {"Paged": ("https://example.org/", "x"), "Renamed": ("https://example.org/", "x")}, clear=True)
@mock.patch(f"{COMMAND}.SOURCES", (fake_github, fake_pypi, fake_page))
@mock.patch("website.github.close_issue")
@mock.patch("website.github.open_issue", side_effect=lambda title, body, label: {"number": 9, "title": title, "state": "open"})
@mock.patch("website.github.issues", side_effect=lambda: [dict(issue) for issue in ISSUES])
class CheckSoftwareVersionsTests(TestCase):
	def setUp(self):
		for name, visible in (
			("Broken", True),
			("Stale", True),
			("Stale", True),  # a duplicate record of the same software
			("Known", True),
			("Current", True),
			("Ahead", True),
			("Lingering", True),
			("Paged", True),
			("Hidden", False),
		):
			version = {"Known": "3.0", "Current": "1.0.0"}.get(name, "1.0")
			software = make_software(name, version, code_repository_url=f"https://github.com/example/{name.lower()}")
			if visible:
				VerifiedSoftware.create_verified(software)

	def test_opens_one_issue_per_new_version_and_closes_the_one_it_supersedes(self, issues, open_issue, close_issue):
		err = StringIO()
		call_command("check_software_versions", "--open-issues", stdout=StringIO(), stderr=err)

		self.assertIn("Broken: unreachable", err.getvalue())
		self.assertIn("Broken: 'releases'", err.getvalue())
		self.assertIn("Paged: https://example.org/", err.getvalue())
		self.assertIn("Renamed: No visible software has this name.", err.getvalue())
		self.assertEqual(open_issue.call_count, 3)
		opened = {call.args[0]: call.args[1:] for call in open_issue.call_args_list}
		self.assertEqual(opened.keys(), {
			"New version of Stale: v2.0", "Can't read the version of Paged", "Can't read the version of Renamed",
		})
		body, label = opened["New version of Stale: v2.0"]
		self.assertIn("new version on github.com", body)
		self.assertIn("https://github.com/example/stale/releases/tag/v2.0", body)
		self.assertIn("HSSI lists version 1.0.", body)
		self.assertEqual(label, LABEL)
		body, label = opened["Can't read the version of Paged"]
		self.assertIn("`PAGES`", body)
		self.assertEqual(label, "bug")
		self.assertCountEqual(
			[call.args for call in close_issue.call_args_list],
			[(7, "Superseded by #9."), (13, "Superseded by #12.")],
		)

	def test_opens_no_second_issue_for_a_page_that_is_still_broken(self, issues, open_issue, close_issue):
		issues.side_effect = lambda: [dict(issue) for issue in ISSUES] + [
			{"number": 10, "title": "Can't read the version of Paged", "state": "open"},
		]
		call_command("check_software_versions", "--open-issues", stdout=StringIO(), stderr=StringIO())

		self.assertNotIn("Can't read the version of Paged", [call.args[0] for call in open_issue.call_args_list])

	def test_lists_new_versions_without_opening_issues_by_default(self, issues, open_issue, close_issue):
		out = StringIO()
		call_command("check_software_versions", stdout=out, stderr=StringIO())

		self.assertIn("New version of Stale: v2.0 (HSSI lists version 1.0)", out.getvalue())
		self.assertIn("New version of Known: 3.1 (HSSI lists version 3.0)", out.getvalue())
		self.assertNotIn("Hidden", out.getvalue())
		self.assertNotIn("Current", out.getvalue())
		issues.assert_not_called()
		open_issue.assert_not_called()
		close_issue.assert_not_called()


@override_settings(HSSI_GITHUB_TOKEN="token")
@mock.patch("website.github.open_issue")
class SubmissionIssueTests(TestCase):
	def _submit(self):
		form = {
			"software_name": "Submitted",
			"codeRepositoryURL": "https://github.com/example/submitted",
			"submitterName": {"submitterName": "Ada Lovelace", "submitterEmail": "ada@example.com"},
			"software_functionality": [],
		}
		with self.captureOnCommitCallbacks(execute=True):
			response = self.client.post(
				"/submit/submit_data/", data=json.dumps(form), content_type="application/json",
			)
		self.assertEqual(response.status_code, 302)

	def test_form_submission_opens_an_issue_without_submitter_details(self, open_issue):
		self._submit()

		title, body, label = open_issue.call_args.args
		self.assertEqual(title, "New submission: Submitted")
		self.assertIn('"codeRepositoryUrl": "https://github.com/example/submitted"', body)
		self.assertNotIn("ada@example.com", body)
		self.assertNotIn("Lovelace", body)
		self.assertEqual(label, "new submission")

	def test_github_failure_does_not_fail_the_submission(self, open_issue):
		open_issue.side_effect = requests.ConnectionError
		with self.assertLogs("django", "ERROR"):
			self._submit()

	@mock.patch("website.views.submit.email_existing_edit_link", side_effect=OSError)
	def test_email_failure_does_not_stop_the_issue(self, email, open_issue):
		with self.assertRaises(OSError):
			self._submit()
		open_issue.assert_called_once()

	@override_settings(HSSI_GITHUB_TOKEN=None)
	def test_no_issue_without_a_token(self, open_issue):
		self._submit()
		open_issue.assert_not_called()
