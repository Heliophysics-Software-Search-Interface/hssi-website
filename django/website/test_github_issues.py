from io import StringIO
from unittest import mock

import requests
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings

from . import github
from .management.commands.check_software_versions import LABEL, is_newer
from .models import Software, SoftwareVersion, VerifiedSoftware


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
		):
			with self.subTest(tag=tag, current=current):
				self.assertEqual(is_newer(tag, current), expected)


class GitHubClientTests(SimpleTestCase):
	@mock.patch("website.github.requests.get")
	def test_reads_owner_and_repo_from_the_url(self, get):
		get.return_value.status_code = 200
		for url in (
			"https://github.com/sunpy/sunpy",
			"https://github.com/sunpy/sunpy.git",
			"https://github.com/sunpy/sunpy/tree/main",
			"https://GitHub.com/sunpy/sunpy",
		):
			with self.subTest(url=url):
				github.latest_release(url)
				self.assertEqual(
					get.call_args.args[0],
					"https://api.github.com/repos/sunpy/sunpy/releases/latest",
				)

	@mock.patch("website.github.requests.get")
	def test_repository_without_releases_has_none(self, get):
		get.return_value.status_code = 404
		self.assertIsNone(github.latest_release("https://github.com/example/none"))

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


RELEASES = {
	"https://github.com/example/stale": {"tag_name": "v2.0", "html_url": "https://github.com/example/stale/releases/tag/v2.0"},
	"https://github.com/example/known": {"tag_name": "3.1", "html_url": "https://github.com/example/known/releases/tag/3.1"},
	"https://github.com/example/current": {"tag_name": "v1.0", "html_url": "https://github.com/example/current/releases/tag/v1.0"},
	"https://github.com/example/hidden": {"tag_name": "9.0", "html_url": "https://github.com/example/hidden/releases/tag/9.0"},
}

def fake_latest_release(repo_url: str) -> dict | None:
	if repo_url.endswith("/broken"):
		raise requests.ConnectionError("unreachable")
	return RELEASES.get(repo_url)


ISSUES = [
	{"number": 3, "title": "New version of Stale: v1.2", "state": "closed"},
	{"number": 5, "title": "New version of Known: 3.1", "state": "closed"},
	{"number": 7, "title": "New version of Stale: v1.5", "state": "open"},
	{"number": 8, "title": "New version of Stale Fork: 1.0", "state": "open"},
]


@override_settings(HSSI_GITHUB_TOKEN="token")
@mock.patch("website.github.close_issue")
@mock.patch("website.github.open_issue", return_value={"number": 9})
@mock.patch("website.github.issues", return_value=ISSUES)
@mock.patch("website.github.latest_release", side_effect=fake_latest_release)
class CheckSoftwareVersionsTests(TestCase):
	def setUp(self):
		for name, version, visible in (
			("Broken", "1.0", True),
			("Stale", "1.0", True),
			("Stale", "1.0", True),  # a duplicate record of the same software
			("Known", "3.0", True),
			("Current", "1.0.0", True),
			("Hidden", "1.0", False),
		):
			software = Software.objects.create(
				software_name=name,
				code_repository_url=f"https://github.com/example/{name.lower()}",
			)
			software.version.add(SoftwareVersion.objects.create(number=version))
			if visible:
				VerifiedSoftware.create_verified(software)

	def test_opens_one_issue_per_new_version_and_closes_the_one_it_supersedes(
		self, latest_release, issues, open_issue, close_issue,
	):
		err = StringIO()
		call_command("check_software_versions", "--open-issues", stdout=StringIO(), stderr=err)

		checked = [call.args[0] for call in latest_release.call_args_list]
		self.assertNotIn("https://github.com/example/hidden", checked)
		self.assertIn("Broken: unreachable", err.getvalue())
		open_issue.assert_called_once()
		title, body, label = open_issue.call_args.args
		self.assertEqual(title, "New version of Stale: v2.0")
		self.assertIn("HSSI lists version 1.0.", body)
		self.assertIn("https://github.com/example/stale/releases/tag/v2.0", body)
		self.assertEqual(label, LABEL)
		close_issue.assert_called_once_with(7, "Superseded by #9.")

	def test_lists_new_versions_without_opening_issues_by_default(
		self, latest_release, issues, open_issue, close_issue,
	):
		out = StringIO()
		call_command("check_software_versions", stdout=out, stderr=StringIO())

		self.assertIn("New version of Stale: v2.0 (HSSI lists version 1.0)", out.getvalue())
		self.assertIn("New version of Known: 3.1 (HSSI lists version 3.0)", out.getvalue())
		issues.assert_not_called()
		open_issue.assert_not_called()
		close_issue.assert_not_called()
