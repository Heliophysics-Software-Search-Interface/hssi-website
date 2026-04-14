"""Regression tests for isolated POST updates and repository URL lookup."""

import uuid

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .models import (
	Keyword,
	License,
	RepoStatus,
	Software,
	SubmissionInfo,
	VerifiedSoftware,
)


UPDATE_TOKEN = "test-token-please-ignore"


@override_settings(HSSI_UPDATE_TOKEN=UPDATE_TOKEN)
class SoftwarePostUpdateTests(TestCase):
	"""POST /api/update behavior."""

	@classmethod
	def setUpTestData(cls):
		cls.software = Software.objects.create(
			software_name="Test Software",
			code_repository_url="https://example.com/test",
			description="original",
			documentation="https://docs.example.com/test",
		)
		VerifiedSoftware.create_verified(cls.software)
		cls.submission_info = SubmissionInfo.objects.create(
			software=cls.software,
			submission_date=timezone.now(),
		)
		cls.active_status = RepoStatus.objects.create(name="Active")
		RepoStatus.objects.create(name="Inactive")
		License.objects.create(name="MIT")

	def setUp(self):
		self.client = APIClient()
		self.url = "/api/update"
		self.auth = f"Bearer {UPDATE_TOKEN}"

	def _post(self, fields, auth: str | None = None, software_id: str | None = None):
		body = {
			"softwareId": software_id or str(self.software.id),
			"fields": fields,
		}
		return self._post_body(body, auth=auth)

	def _post_body(self, body, auth: str | None = None):
		kwargs = {"format": "json"}
		header = self.auth if auth is None else auth
		if header:
			kwargs["HTTP_AUTHORIZATION"] = header
		return self.client.post(self.url, data=body, **kwargs)

	def test_scalar_update_sets_fk_field(self):
		response = self._post({"developmentStatus": "Active"})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		self.software.refresh_from_db()
		self.assertEqual(self.software.development_status, self.active_status)
		self.assertEqual(response.data["softwareId"], str(self.software.id))
		self.assertIn("development_status", response.data["fieldsUpdated"])

	def test_m2m_replacement_replaces_keywords(self):
		self.software.keywords.add(Keyword.objects.create(name="old"))

		response = self._post({"keywords": ["alpha", "beta"]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		names = sorted(self.software.keywords.values_list("name", flat=True))
		self.assertEqual(names, ["alpha", "beta"])

	def test_empty_list_clears_m2m(self):
		self.software.keywords.add(Keyword.objects.create(name="old"))
		self.assertEqual(self.software.keywords.count(), 1)

		response = self._post({"keywords": []})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		self.assertEqual(self.software.keywords.count(), 0)

	def test_missing_field_leaves_value_unchanged(self):
		response = self._post({"developmentStatus": "Active"})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		self.software.refresh_from_db()
		self.assertEqual(self.software.description, "original")

	def test_nullable_scalar_can_be_cleared(self):
		response = self._post({"documentation": None})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		self.software.refresh_from_db()
		self.assertIsNone(self.software.documentation)

	def test_unknown_field_rejected(self):
		response = self._post({"notAField": "value"})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("not_a_field", response.data)

	def test_submitter_rejected(self):
		response = self._post({
			"submitter": [{
				"email": "x@y.com",
				"person": {"givenName": "A", "familyName": "B"},
			}],
		})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("submitter", response.data)

	def test_invalid_token_rejected(self):
		response = self._post({"developmentStatus": "Active"}, auth="Bearer wrong")
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_missing_token_rejected(self):
		response = self._post({"developmentStatus": "Active"}, auth="")
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_malformed_auth_header_rejected(self):
		response = self._post({"developmentStatus": "Active"}, auth="Token wrong")
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_updates_modification_description(self):
		response = self._post({"developmentStatus": "Active"})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		self.submission_info.refresh_from_db()
		self.assertIn(
			"development_status",
			self.submission_info.modification_description or "",
		)

	def test_missing_software_id_rejected(self):
		response = self._post_body({"fields": {"developmentStatus": "Active"}})
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("softwareId", response.data)

	def test_invalid_software_id_rejected(self):
		response = self._post({"developmentStatus": "Active"}, software_id="not-a-uuid")
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("softwareId", response.data)

	def test_not_found_for_unknown_uid(self):
		response = self._post(
			{"developmentStatus": "Active"},
			software_id=str(uuid.uuid4()),
		)
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_non_visible_software_returns_404(self):
		hidden = Software.objects.create(software_name="Hidden")

		response = self._post(
			{"developmentStatus": "Active"},
			software_id=str(hidden.id),
		)

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_missing_fields_rejected(self):
		response = self._post_body({"softwareId": str(self.software.id)})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("fields", response.data)

	def test_empty_fields_rejected(self):
		response = self._post({})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("detail", response.data)

	def test_root_array_rejected(self):
		response = self._post_body([{
			"softwareId": str(self.software.id),
			"fields": {"developmentStatus": "Active"},
		}])

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("detail", response.data)

	def test_detail_route_does_not_accept_patch(self):
		response = self.client.patch(
			f"/api/data/software/{self.software.id}/",
			data={"developmentStatus": "Active"},
			format="json",
			HTTP_AUTHORIZATION=self.auth,
		)
		self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


@override_settings(HSSI_UPDATE_TOKEN=None)
class SoftwarePostUpdateTokenUnsetTests(TestCase):
	"""With no token configured, update endpoints fail closed."""

	@classmethod
	def setUpTestData(cls):
		cls.software = Software.objects.create(software_name="Test Software")
		VerifiedSoftware.create_verified(cls.software)

	def test_unset_token_denies_every_update(self):
		client = APIClient()
		response = client.post(
			"/api/update",
			data={
				"softwareId": str(self.software.id),
				"fields": {"developmentStatus": "Active"},
			},
			format="json",
			HTTP_AUTHORIZATION="Bearer anything",
		)
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_unset_token_denies_lookup(self):
		client = APIClient()
		response = client.get(
			"/api/update/lookup",
			{"code_repository_url": "https://example.com/test"},
			HTTP_AUTHORIZATION="Bearer anything",
		)
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(HSSI_UPDATE_TOKEN=UPDATE_TOKEN)
class SoftwareUpdateLookupTests(TestCase):
	"""GET /api/update/lookup with required ?code_repository_url= filter."""

	@classmethod
	def setUpTestData(cls):
		cls.match = Software.objects.create(
			software_name="Matching",
			code_repository_url="https://github.com/example/match",
		)
		VerifiedSoftware.create_verified(cls.match)

		cls.other = Software.objects.create(
			software_name="Other",
			code_repository_url="https://github.com/example/other",
		)
		VerifiedSoftware.create_verified(cls.other)

		cls.hidden = Software.objects.create(
			software_name="Hidden",
			code_repository_url="https://github.com/example/match",
		)

		cls.branch_root = Software.objects.create(
			software_name="Branch Root",
			code_repository_url="https://github.com/example/branch",
		)
		VerifiedSoftware.create_verified(cls.branch_root)

		cls.branch_path = Software.objects.create(
			software_name="Branch Path",
			code_repository_url="https://github.com/example/branch/tree/dev",
		)
		VerifiedSoftware.create_verified(cls.branch_path)

		cls.gitlab = Software.objects.create(
			software_name="GitLab Nested",
			code_repository_url="https://gitlab.com/group/subgroup/project",
		)
		VerifiedSoftware.create_verified(cls.gitlab)

	def setUp(self):
		self.client = APIClient()
		self.url = "/api/update/lookup"
		self.auth = f"Bearer {UPDATE_TOKEN}"

	def _lookup(self, url: str, auth: str | None = None):
		kwargs = {"HTTP_AUTHORIZATION": self.auth if auth is None else auth}
		return self.client.get(
			self.url,
			{"code_repository_url": url},
			**kwargs,
		)

	def _lookup_names(self, url: str) -> list[str]:
		response = self._lookup(url)
		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		return [entry["softwareName"] for entry in response.data["data"]]

	def test_exact_lookup_returns_matching_software(self):
		response = self._lookup("https://github.com/example/match")

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		self.assertEqual(response.data["data"][0]["softwareName"], "Matching")
		self.assertEqual(
			response.data["data"][0]["codeRepositoryUrl"],
			"https://github.com/example/match",
		)

	def test_lookup_is_case_insensitive(self):
		names = self._lookup_names("HTTPS://GitHub.com/example/MATCH")
		self.assertEqual(names, ["Matching"])

	def test_trailing_slash_lookup_matches_root_url(self):
		names = self._lookup_names("https://github.com/example/match/")
		self.assertEqual(names, ["Matching"])

	def test_git_suffix_lookup_matches_root_url(self):
		names = self._lookup_names("https://github.com/example/match.git")
		self.assertEqual(names, ["Matching"])

	def test_github_branch_url_lookup_returns_all_normalized_matches(self):
		names = self._lookup_names("https://github.com/example/branch/tree/main")
		self.assertEqual(names, ["Branch Path", "Branch Root"])

	def test_gitlab_tree_url_lookup_matches_nested_project(self):
		names = self._lookup_names(
			"https://gitlab.com/group/subgroup/project/-/tree/main"
		)
		self.assertEqual(names, ["GitLab Nested"])

	def test_unknown_lookup_returns_empty(self):
		names = self._lookup_names("https://github.com/example/nothing")
		self.assertEqual(names, [])

	def test_lookup_requires_token(self):
		response = self._lookup("https://github.com/example/match", auth="")
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_lookup_requires_code_repository_url(self):
		response = self.client.get(
			self.url,
			HTTP_AUTHORIZATION=self.auth,
		)

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("codeRepositoryUrl", response.data)

	def test_lookup_excludes_hidden_software(self):
		names = self._lookup_names("https://github.com/example/match")
		self.assertEqual(names, ["Matching"])
