"""Regression tests for PATCH /api/data/software/<uid>/ and its lookup sibling.

These tests exercise the partial update endpoint and its authentication
gate end-to-end through the DRF router, using the SubmissionSerializer's
USER view in partial mode. They assume a Postgres test database is
available (Django creates one automatically via ``manage.py test``).
"""

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
class SoftwarePartialUpdateTests(TestCase):
	"""PATCH /api/data/software/<uid>/ behavior under the USER view."""

	@classmethod
	def setUpTestData(cls):
		cls.software = Software.objects.create(
			software_name="Test Software",
			code_repository_url="https://example.com/test",
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
		self.url = f"/api/data/software/{self.software.id}/"
		self.auth = f"Bearer {UPDATE_TOKEN}"

	def _patch(self, data, auth: str | None = None):
		kwargs = {"format": "json"}
		header = self.auth if auth is None else auth
		if header:
			kwargs["HTTP_AUTHORIZATION"] = header
		return self.client.patch(self.url, data=data, **kwargs)

	def test_scalar_update_sets_fk_field(self):
		response = self._patch({"developmentStatus": "Active"})
		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		self.software.refresh_from_db()
		self.assertEqual(self.software.development_status, self.active_status)
		self.assertIn("development_status", response.data["fieldsUpdated"])

	def test_m2m_replacement_replaces_keywords(self):
		self.software.keywords.add(Keyword.objects.create(name="old"))

		response = self._patch({"keywords": ["alpha", "beta"]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		names = sorted(self.software.keywords.values_list("name", flat=True))
		self.assertEqual(names, ["alpha", "beta"])

	def test_empty_list_clears_m2m(self):
		self.software.keywords.add(Keyword.objects.create(name="old"))
		self.assertEqual(self.software.keywords.count(), 1)

		response = self._patch({"keywords": []})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		self.assertEqual(self.software.keywords.count(), 0)

	def test_missing_field_leaves_value_unchanged(self):
		self.software.description = "original"
		self.software.save()

		response = self._patch({"developmentStatus": "Active"})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		self.software.refresh_from_db()
		self.assertEqual(self.software.description, "original")

	def test_unknown_field_rejected(self):
		response = self._patch({"notAField": "value"})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		# decamelize turns notAField into not_a_field before validation
		self.assertIn("not_a_field", response.data)

	def test_submitter_rejected(self):
		response = self._patch({
			"submitter": [{
				"email": "x@y.com",
				"person": {"givenName": "A", "familyName": "B"},
			}],
		})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("submitter", response.data)

	def test_invalid_token_rejected(self):
		response = self._patch({"developmentStatus": "Active"}, auth="Bearer wrong")
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_missing_token_rejected(self):
		response = self._patch({"developmentStatus": "Active"}, auth="")
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_malformed_auth_header_rejected(self):
		response = self._patch({"developmentStatus": "Active"}, auth="Token wrong")
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_updates_modification_description(self):
		response = self._patch({"developmentStatus": "Active"})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		self.submission_info.refresh_from_db()
		self.assertIn(
			"development_status",
			self.submission_info.modification_description or "",
		)

	def test_not_found_for_unknown_uid(self):
		response = self.client.patch(
			f"/api/data/software/{uuid.uuid4()}/",
			data={"developmentStatus": "Active"},
			format="json",
			HTTP_AUTHORIZATION=self.auth,
		)
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_non_visible_software_returns_404(self):
		hidden = Software.objects.create(software_name="Hidden")
		# no VerifiedSoftware entry — not visible
		response = self.client.patch(
			f"/api/data/software/{hidden.id}/",
			data={"developmentStatus": "Active"},
			format="json",
			HTTP_AUTHORIZATION=self.auth,
		)
		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@override_settings(HSSI_UPDATE_TOKEN=None)
class SoftwarePartialUpdateTokenUnsetTests(TestCase):
	"""With no token configured, PATCH must fail closed for every request."""

	@classmethod
	def setUpTestData(cls):
		cls.software = Software.objects.create(software_name="Test Software")
		VerifiedSoftware.create_verified(cls.software)

	def test_unset_token_denies_every_patch(self):
		client = APIClient()
		response = client.patch(
			f"/api/data/software/{self.software.id}/",
			data={"developmentStatus": "Active"},
			format="json",
			HTTP_AUTHORIZATION="Bearer anything",
		)
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class SoftwareListLookupTests(TestCase):
	"""GET /api/list/software/ with an optional ?repo_url= filter."""

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
		# no VerifiedSoftware entry for this one

	def setUp(self):
		self.client = APIClient()

	def test_repo_url_lookup_returns_matching_software(self):
		response = self.client.get(
			"/api/list/software/",
			{"repo_url": "https://github.com/example/match"},
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data["data"]), 1)
		self.assertEqual(response.data["data"][0]["name"], "Matching")

	def test_repo_url_is_case_insensitive(self):
		response = self.client.get(
			"/api/list/software/",
			{"repo_url": "HTTPS://GitHub.com/example/MATCH"},
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data["data"]), 1)

	def test_repo_url_unknown_returns_empty(self):
		response = self.client.get(
			"/api/list/software/",
			{"repo_url": "https://github.com/example/nothing"},
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["data"], [])

	def test_no_filter_returns_visible_software_only(self):
		response = self.client.get("/api/list/software/")
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		names = [entry["name"] for entry in response.data["data"]]
		self.assertIn("Matching", names)
		self.assertIn("Other", names)
		self.assertNotIn("Hidden", names)
