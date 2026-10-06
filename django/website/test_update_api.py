"""Regression tests for PATCH /api/data/software/<uid>/ and its lookup sibling.

These tests exercise the partial update endpoint and its authentication
gate end-to-end through the DRF router, using the SubmissionSerializer's
USER view in partial mode. They assume a Postgres test database is
available (Django creates one automatically via ``manage.py test``).
"""

import datetime, json, uuid
from urllib.parse import urlsplit

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from .models import (
	Keyword,
	License,
	Person,
	RepoStatus,
	Software,
	SoftwareEditQueue,
	SoftwareVersion,
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

	def test_every_entry_carries_its_slug(self):
		response = self.client.get("/api/list/software/")
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		slugs = {entry["name"]: entry["slug"] for entry in response.data["data"]}
		self.assertEqual(slugs["Matching"], "matching")
		self.assertEqual(slugs["Other"], "other")

	def test_listed_slug_resolves_on_the_detail_endpoint(self):
		"""A display name is not a usable key; the slug shipped beside it is.

		"PyMap3D" slugs to "pymap3d", so a consumer reading `name` off this
		endpoint and substituting it into the detail URL gets nothing back.
		Reading `slug` instead round-trips.
		"""
		software = Software.objects.create(
			software_name="PyMap3D",
			code_repository_url="https://github.com/example/pymap3d",
		)
		VerifiedSoftware.create_verified(software)

		response = self.client.get("/api/list/software/")
		entry = next(
			item for item in response.data["data"] if item["name"] == "PyMap3D"
		)
		self.assertEqual(entry["slug"], "pymap3d")
		self.assertNotEqual(entry["slug"], entry["name"])

		detail = self.client.get(f"/api/view/software/{entry['slug']}/?view=jsonld")
		self.assertEqual(detail.status_code, status.HTTP_200_OK)
		self.assertEqual(detail.json()["name"], "PyMap3D")


class SoftwareListJsonLdDumpTests(TestCase):
	"""GET /api/list/software/?view=jsonld returns all records' JSON-LD."""

	@classmethod
	def setUpTestData(cls):
		for name, repo in (
			("Matching", "https://github.com/example/match"),
			("Other", "https://github.com/example/other"),
		):
			software = Software.objects.create(
				software_name=name,
				code_repository_url=repo,
			)
			VerifiedSoftware.create_verified(software)
		Software.objects.create(
			software_name="Hidden",
			code_repository_url="https://github.com/example/hidden",
		)

	def setUp(self):
		self.client = APIClient()

	def test_jsonld_view_dumps_every_visible_record(self):
		response = self.client.get("/api/list/software/", {"view": "jsonld"})
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		data = response.json()["data"]
		self.assertEqual([entry["name"] for entry in data], ["Matching", "Other"])
		for entry in data:
			self.assertIn("@context", entry)
			self.assertIn("codeRepository", entry)

	def test_jsonld_view_matches_the_detail_endpoint_output(self):
		"""The dump is the same serialization as /api/view/, just batched."""
		dump = self.client.get("/api/list/software/", {"view": "jsonld"})
		entry = dump.json()["data"][0]
		software_id = VerifiedSoftware.objects.get(slug="matching").pk
		detail = self.client.get(f"/api/view/software/{software_id}/?view=jsonld")
		self.assertEqual(entry, detail.json())

	def test_jsonld_view_composes_with_repo_url_filter(self):
		response = self.client.get(
			"/api/list/software/",
			{"view": "jsonld", "repo_url": "https://github.com/example/match"},
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		data = response.json()["data"]
		self.assertEqual(len(data), 1)
		self.assertEqual(data[0]["name"], "Matching")

	def test_subject_of_id_links_to_the_slug_detail_endpoint(self):
		"""`subjectOf.@id` must be a fetchable URL, keyed on the slug.

		It was built by interpolating the VerifiedSoftware row itself, whose
		`__str__` is the display name, so "PySPEDAS" produced
		`/api/view/software/PySPEDAS/`, a 404 for most of the catalog.
		"""
		software = Software.objects.create(
			software_name="PySPEDAS",
			code_repository_url="https://github.com/example/pyspedas",
		)
		VerifiedSoftware.create_verified(software)
		software.version.add(SoftwareVersion.objects.create(number="1.0.0"))

		dump = self.client.get("/api/list/software/", {"view": "jsonld"})
		entry = next(
			item for item in dump.json()["data"] if item["name"] == "PySPEDAS"
		)
		subject_id = entry["subjectOf"]["@id"]
		self.assertIn("/api/view/software/pyspedas/", subject_id)
		self.assertNotIn("PySPEDAS", subject_id)

		parts = urlsplit(subject_id)
		detail = self.client.get(f"{parts.path}?{parts.query}")
		self.assertEqual(detail.status_code, status.HTTP_200_OK)
		self.assertEqual(detail.json()["name"], "PySPEDAS")

	def test_unsupported_view_returns_400(self):
		for bad in ("json-ld", "user", "standard", "nonsense"):
			with self.subTest(view=bad):
				response = self.client.get("/api/list/software/", {"view": bad})
				self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(HSSI_UPDATE_TOKEN=UPDATE_TOKEN)
class SoftwareDateModifiedTests(TestCase):
	"""`Software.date_modified` is stamped only by the supported write paths.

	See issue #103 for the paths that stamp and the ones that deliberately
	do not.
	"""

	SUBMITTER = {"email": "ada@example.com", "person": {"givenName": "Ada", "familyName": "Lovelace"}}
	AUTHOR = {"givenName": "Ada", "familyName": "Lovelace"}

	def setUp(self):
		self.client = APIClient()
		self.software = Software.objects.create(
			software_name="Stamped",
			code_repository_url="https://github.com/example/stamped",
		)
		VerifiedSoftware.create_verified(self.software)
		self.submission_info = SubmissionInfo.objects.create(
			software=self.software,
			submission_date=timezone.make_aware(datetime.datetime(2025, 1, 1)),
		)
		RepoStatus.objects.create(name="Active")

	def _jsonld(self, software: Software) -> dict:
		response = self.client.get(f"/api/view/software/{software.id}/", {"view": "jsonld"})
		self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)
		return response.json()

	# JSON-LD output ---------------------------------------------------------

	def test_jsonld_falls_back_to_submission_date_while_unstamped(self):
		self.software.version.add(SoftwareVersion.objects.create(number="1.0"))
		self.assertIsNone(self.software.date_modified)
		self.assertTrue(
			self._jsonld(self.software)["subjectOf"]["dateModified"].startswith("2025-01-01")
		)

	def test_jsonld_prefers_the_stamp_once_set(self):
		self.software.version.add(SoftwareVersion.objects.create(number="1.0"))
		Software.objects.filter(pk=self.software.pk).update(
			date_modified=timezone.make_aware(datetime.datetime(2026, 6, 15, 12, 0))
		)
		self.assertTrue(
			self._jsonld(self.software)["subjectOf"]["dateModified"].startswith("2026-06-15")
		)

	# API write paths --------------------------------------------------------

	def test_patch_stamps(self):
		before = timezone.now()
		response = self.client.patch(
			f"/api/data/software/{self.software.id}/",
			data={"developmentStatus": "Active"},
			format="json",
			HTTP_AUTHORIZATION=f"Bearer {UPDATE_TOKEN}",
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		self.software.refresh_from_db()
		self.assertIsNotNone(self.software.date_modified)
		self.assertGreaterEqual(self.software.date_modified, before)

	def test_submission_api_stamps_new_record(self):
		before = timezone.now()
		response = self.client.post(
			"/api/submission/",
			data=[{
				"submitter": [self.SUBMITTER],
				"softwareName": "Created via API",
				"codeRepositoryUrl": "https://github.com/example/created",
				"authors": [self.AUTHOR],
				"description": "A description.",
			}],
			format="json",
		)
		self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
		created = Software.objects.get(software_name="Created via API")
		self.assertIsNotNone(created.date_modified)
		self.assertGreaterEqual(created.date_modified, before)

	# Submission parser (public form, legacy /api/submit, edit link) ---------

	def _form_dict(self, name: str) -> dict:
		return {
			"software_name": name,
			"codeRepositoryURL": "https://github.com/example/parsed",
			"submitterName": {"submitterName": "Ada Lovelace", "submitterEmail": "ada@example.com"},
			"software_functionality": [],
		}

	def test_parser_stamps_create_and_edit(self):
		from .data_parser import handle_submission_data

		before = timezone.now()
		submission_id = handle_submission_data(self._form_dict("Parsed"))
		created = SubmissionInfo.objects.get(pk=submission_id).software
		self.assertGreaterEqual(created.date_modified, before)

		old = timezone.make_aware(datetime.datetime(2020, 1, 1))
		Software.objects.filter(pk=created.pk).update(date_modified=old)
		handle_submission_data(self._form_dict("Parsed, edited"), created)
		created.refresh_from_db()
		self.assertEqual(created.software_name, "Parsed, edited")
		self.assertGreater(created.date_modified, old)

	def test_edit_link_failure_rolls_back_metadata_and_stamp(self):
		from unittest import mock

		queue_item = SoftwareEditQueue.create(self.software)
		with mock.patch(
			"website.data_parser.apply_related_observatories",
			side_effect=RuntimeError("boom"),
		):
			response = self.client.post(
				f"/curate/edit_submission/submit_data/{queue_item.id}/",
				data=json.dumps(self._form_dict("Should not persist")),
				content_type="application/json",
			)
		self.assertEqual(response.status_code, 500)
		self.software.refresh_from_db()
		self.assertEqual(self.software.software_name, "Stamped")
		self.assertIsNone(self.software.date_modified)

	# Admin change form ------------------------------------------------------

	def _admin_form(self, software: Software):
		from django.contrib.auth import get_user_model
		from django.test import RequestFactory
		from .admin.hssi_admin_site import admin_site
		from .admin.model_admin import SoftwareAdmin

		request = RequestFactory().get("/")
		request.user = get_user_model().objects.create_superuser("curator", "c@example.com", "pw")
		model_admin = SoftwareAdmin(Software, admin_site)
		form_class = model_admin.get_form(request, software, change=True)
		initial = form_class(instance=software)
		data = {
			name: initial[name].value()
			for name in initial.fields
			if initial[name].value() not in (None, "", [])
		}
		return request, model_admin, form_class, data

	def _admin_save(self, request, model_admin, form_class, data, software):
		form = form_class(data, instance=software)
		self.assertTrue(form.is_valid(), form.errors)
		# Same sequence as ModelAdmin._changeform_view: save_form attaches
		# form.save_m2m, which save_related then calls.
		new_object = model_admin.save_form(request, form, change=True)
		model_admin.save_model(request, new_object, form, True)
		model_admin.save_related(request, form, [], True)
		software.refresh_from_db()

	def test_admin_save_without_changes_does_not_stamp(self):
		ada = Person.objects.create(given_name="Ada", family_name="Lovelace")
		self.software.authors.set([ada])
		request, model_admin, form_class, data = self._admin_form(self.software)

		self._admin_save(request, model_admin, form_class, data, self.software)
		self.assertIsNone(self.software.date_modified)

	def test_admin_scalar_change_stamps(self):
		ada = Person.objects.create(given_name="Ada", family_name="Lovelace")
		self.software.authors.set([ada])
		request, model_admin, form_class, data = self._admin_form(self.software)

		data["description"] = "Edited by a curator."
		self._admin_save(request, model_admin, form_class, data, self.software)
		self.assertIsNotNone(self.software.date_modified)

	def test_admin_author_reorder_stamps(self):
		ada = Person.objects.create(given_name="Ada", family_name="Lovelace")
		grace = Person.objects.create(given_name="Grace", family_name="Hopper")
		self.software.authors.set([ada, grace])
		request, model_admin, form_class, data = self._admin_form(self.software)

		data["authors"] = [grace.pk, ada.pk]
		self._admin_save(request, model_admin, form_class, data, self.software)
		self.assertIsNotNone(self.software.date_modified)
		self.assertEqual(list(self.software.authors.all()), [grace, ada])
