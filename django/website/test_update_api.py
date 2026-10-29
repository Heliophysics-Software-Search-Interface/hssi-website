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
	Award,
	Keyword,
	License,
	Organization,
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


@override_settings(HSSI_UPDATE_TOKEN=UPDATE_TOKEN)
class SharedRowTestCase(TestCase):
	"""Base for tests of rows that other software entries may share."""

	ORCID = "https://orcid.org/0000-0000-0000-0001"
	OTHER_ORCID = "https://orcid.org/0000-0000-0000-0002"
	NASA = {"name": "NASA", "identifier": "https://ror.org/027ka1x80"}

	@classmethod
	def setUpTestData(cls):
		cls.software = Software.objects.create(
			software_name="Shared Rows",
			code_repository_url="https://example.com/shared",
		)
		VerifiedSoftware.create_verified(cls.software)

	def setUp(self):
		self.client = APIClient()

	def _patch(self, data):
		return self.client.patch(
			f"/api/data/software/{self.software.id}/",
			data=data,
			format="json",
			HTTP_AUTHORIZATION=f"Bearer {UPDATE_TOKEN}",
		)

	def _post(self, **fields):
		return self.client.post("/api/submission/", data=[{
			"submitter": [{"email": "ada@example.com", "person": {"givenName": "Ada", "familyName": "Lovelace"}}],
			"softwareName": "Created via API",
			"codeRepositoryUrl": "https://github.com/example/created",
			"authors": [{"givenName": "Ada", "familyName": "Lovelace"}],
			"description": "A description.",
			**fields,
		}], format="json")


class PersonRowTests(SharedRowTestCase):
	"""How authors resolve to Person rows."""

	def test_identifier_attaches_to_unidentified_current_author(self):
		for stored, orcid in ((None, self.ORCID), ("", self.OTHER_ORCID)):
			with self.subTest(stored_identifier=stored):
				person = Person.objects.create(given_name="Ann", family_name="Lee", identifier=stored)
				self.software.authors.set([person])
				people_before = Person.objects.count()

				response = self._patch({"authors": [
					{"givenName": "Ann", "familyName": "Lee", "identifier": orcid},
				]})

				self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
				person.refresh_from_db()
				self.assertEqual(person.identifier, orcid)
				self.assertEqual(list(self.software.authors.all()), [person])
				self.assertEqual(Person.objects.count(), people_before)

	def test_identifier_attaches_across_a_different_split(self):
		person = Person.objects.create(given_name="Maria de", family_name="Souza", identifier="")
		self.software.authors.set([person])
		people_before = Person.objects.count()

		response = self._patch({"authors": [
			{"givenName": "Maria", "familyName": "de Souza", "identifier": self.ORCID},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		person.refresh_from_db()
		self.assertEqual(person.identifier, self.ORCID)
		self.assertEqual(list(self.software.authors.all()), [person])
		self.assertEqual(Person.objects.count(), people_before)

	def test_identifier_attaches_ignoring_case(self):
		person = Person.objects.create(given_name="Darren de", family_name="Zeeuw", identifier="")
		self.software.authors.set([person])

		response = self._patch({"authors": [
			{"givenName": "Darren", "familyName": "De Zeeuw", "identifier": self.ORCID},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		person.refresh_from_db()
		self.assertEqual(person.identifier, self.ORCID)
		self.assertEqual((person.given_name, person.family_name), ("Darren", "De Zeeuw"))
		self.assertEqual(list(self.software.authors.all()), [person])

	def test_identifier_never_replaces_a_different_identifier(self):
		person = Person.objects.create(given_name="Ann", family_name="Lee", identifier=self.OTHER_ORCID)
		self.software.authors.set([person])

		response = self._patch({"authors": [
			{"givenName": "Ann", "familyName": "Lee", "identifier": self.ORCID},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		person.refresh_from_db()
		self.assertEqual(person.identifier, self.OTHER_ORCID)
		author = self.software.authors.get()
		self.assertNotEqual(author.pk, person.pk)
		self.assertEqual(author.identifier, self.ORCID)

	def test_identifier_ignores_namesakes_outside_this_software(self):
		namesake = Person.objects.create(given_name="Ann", family_name="Lee", identifier="")
		other = Software.objects.create(software_name="Other")
		other.authors.set([namesake])

		response = self._patch({"authors": [
			{"givenName": "Ann", "familyName": "Lee", "identifier": self.ORCID},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		namesake.refresh_from_db()
		self.assertEqual(namesake.identifier, "")
		author = self.software.authors.get()
		self.assertNotEqual(author.pk, namesake.pk)
		self.assertEqual(author.identifier, self.ORCID)

	def test_identifier_rejected_when_several_current_authors_match(self):
		split_one = Person.objects.create(given_name="Maria de", family_name="Souza", identifier="")
		split_two = Person.objects.create(given_name="Maria", family_name="de Souza", identifier="")
		self.software.authors.set([split_one, split_two])
		people_before = Person.objects.count()

		payloads = (
			[{"givenName": "Maria", "familyName": "de Souza", "identifier": self.ORCID}],
			[
				{"givenName": "Maria de", "familyName": "Souza"},
				{"givenName": "Maria", "familyName": "de Souza", "identifier": self.ORCID},
			],
		)
		for authors in payloads:
			with self.subTest(authors=len(authors)):
				response = self._patch({"authors": authors})

				self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
				self.assertIn("identifier", response.data)
		for person in (split_one, split_two):
			person.refresh_from_db()
			self.assertEqual(person.identifier, "")
		self.assertEqual(Person.objects.count(), people_before)
		self.assertEqual(list(self.software.authors.all()), [split_one, split_two])

	def test_identified_author_takes_resplit_of_same_full_name(self):
		person = Person.objects.create(given_name="Maria de", family_name="Souza", identifier=self.ORCID)
		self.software.authors.set([person])

		response = self._patch({"authors": [
			{"givenName": "Maria", "familyName": "de Souza", "identifier": self.ORCID},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		person.refresh_from_db()
		self.assertEqual((person.given_name, person.family_name), ("Maria", "de Souza"))
		self.assertEqual(list(self.software.authors.all()), [person])

	def test_same_full_name_ignores_case_and_hyphens(self):
		renames = [
			(("Darren de", "Zeeuw"), ("Darren", "De Zeeuw"), "https://orcid.org/0000-0000-0000-0011"),
			(("Ana Pires De", "Lima"), ("Ana", "Pires de Lima"), "https://orcid.org/0000-0000-0000-0012"),
			(("Lea", "Barrous Dume"), ("Lea", "Barrous-Dume"), "https://orcid.org/0000-0000-0000-0013"),
		]
		people = [
			Person.objects.create(given_name=given, family_name=family, identifier=orcid)
			for (given, family), _, orcid in renames
		]
		Software.objects.create(software_name="Other").authors.set(people)
		self.software.authors.set(people)

		response = self._patch({"authors": [
			{"givenName": given, "familyName": family, "identifier": orcid}
			for _, (given, family), orcid in renames
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		for person, (_, sent, _) in zip(people, renames):
			person.refresh_from_db()
			self.assertEqual((person.given_name, person.family_name), sent)

	def test_identifier_attaches_ignoring_accents(self):
		person = Person.objects.create(given_name="Jose", family_name="Garcia", identifier="")
		self.software.authors.set([person])

		response = self._patch({"authors": [
			{"givenName": "José", "familyName": "García", "identifier": self.ORCID},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		person.refresh_from_db()
		self.assertEqual(person.identifier, self.ORCID)
		self.assertEqual((person.given_name, person.family_name), ("José", "García"))
		self.assertEqual(list(self.software.authors.all()), [person])

	def test_same_full_name_ignores_accents_and_their_encoding(self):
		# The stored é is "e" plus a combining accent; the sent é is one character.
		person = Person.objects.create(given_name="Rene\u0301", family_name="Dupont", identifier=self.ORCID)
		self.software.authors.set([person])

		response = self._patch({"authors": [
			{"givenName": "Ren\u00e9", "familyName": "Dupont", "identifier": self.ORCID},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		person.refresh_from_db()
		self.assertEqual(person.given_name, "Ren\u00e9")

	def test_sent_names_with_fewer_accents_are_not_applied(self):
		unidentified = Person.objects.create(given_name="José", family_name="García", identifier="")
		identified = Person.objects.create(given_name="Zoë", family_name="Brontë", identifier=self.OTHER_ORCID)
		self.software.authors.set([unidentified, identified])

		response = self._patch({"authors": [
			{"givenName": "Jose", "familyName": "Garcia", "identifier": self.ORCID},
			{"givenName": "Zoë", "familyName": "Bronte", "identifier": self.OTHER_ORCID},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		unidentified.refresh_from_db()
		identified.refresh_from_db()
		self.assertEqual(
			(unidentified.given_name, unidentified.family_name, unidentified.identifier),
			("José", "García", self.ORCID),
		)
		self.assertEqual((identified.given_name, identified.family_name), ("Zoë", "Brontë"))
		self.assertEqual(list(self.software.authors.all()), [unidentified, identified])

	def test_unidentified_author_takes_identifier_and_resplit_together(self):
		person = Person.objects.create(given_name="Maria de", family_name="Souza", identifier="")
		self.software.authors.set([person])

		response = self._patch({"authors": [
			{"givenName": "Maria", "familyName": "de Souza", "identifier": self.ORCID},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		person.refresh_from_db()
		self.assertEqual(person.identifier, self.ORCID)
		self.assertEqual((person.given_name, person.family_name), ("Maria", "de Souza"))

	def test_identified_author_keeps_names_when_full_name_differs(self):
		person = Person.objects.create(given_name="Maria de", family_name="Souza", identifier=self.ORCID)
		self.software.authors.set([person])

		response = self._patch({"authors": [
			{"givenName": "Mary", "familyName": "de Souza", "identifier": self.ORCID},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		person.refresh_from_db()
		self.assertEqual((person.given_name, person.family_name), ("Maria de", "Souza"))

	def test_blank_given_name_resolves_to_that_current_author(self):
		tiger = Person.objects.create(given_name="", family_name="Tiger")
		self.software.authors.set([tiger])

		response = self._patch({"authors": [
			{"givenName": "", "familyName": "Tiger"},
			{"givenName": "Ann", "familyName": "Lee"},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		names = [(p.pk == tiger.pk, p.family_name) for p in self.software.authors.all()]
		self.assertEqual(names, [(True, "Tiger"), (False, "Lee")])

	def test_blank_given_name_fills_an_unheld_identifier(self):
		tiger = Person.objects.create(given_name="", family_name="Tiger")
		lion = Person.objects.create(given_name="", family_name="Lion")
		Person.objects.create(given_name="Ann", family_name="Lee", identifier=self.OTHER_ORCID)
		self.software.authors.set([tiger, lion])

		response = self._patch({"authors": [
			{"familyName": "Tiger", "identifier": self.ORCID},
			{"familyName": "Lion", "identifier": self.OTHER_ORCID},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		tiger.refresh_from_db()
		lion.refresh_from_db()
		self.assertEqual(tiger.identifier, self.ORCID)
		self.assertIsNone(lion.identifier)

	def test_blank_given_name_rejected_unless_one_current_author_matches(self):
		Person.objects.create(given_name="", family_name="Tiger")
		twins = [Person.objects.create(given_name="", family_name="Lion") for _ in range(2)]
		self.software.authors.set(twins)
		people_before = Person.objects.count()

		for family in ("Tiger", "Lion"):
			with self.subTest(family=family):
				response = self._patch({"authors": [{"givenName": "", "familyName": family}]})

				self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
				self.assertIn("givenName", response.data)
		self.assertEqual(Person.objects.count(), people_before)
		self.assertEqual(list(self.software.authors.all()), twins)

	def test_submission_api_rejects_blank_given_name(self):
		response = self._post(authors=[{"givenName": "", "familyName": "Tiger"}])

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("givenName", response.data)

	def test_same_person_listed_twice_rejected(self):
		person = Person.objects.create(given_name="Ann", family_name="Lee", identifier=self.ORCID)
		self.software.authors.set([person])
		same_identifier = [
			{"givenName": "Ann", "familyName": "Lee", "identifier": self.ORCID},
			{"givenName": "A.", "familyName": "Lee", "identifier": self.ORCID},
		]
		same_name = [{"givenName": "Ben", "familyName": "Ng"}, {"givenName": "Ben", "familyName": "Ng"}]

		for request in (
			lambda: self._patch({"authors": same_identifier}),
			lambda: self._patch({"authors": same_name}),
			lambda: self._post(authors=same_identifier),
		):
			response = request()

			self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
			self.assertIn("authors", response.data)
		person.refresh_from_db()
		self.assertEqual((person.given_name, person.family_name), ("Ann", "Lee"))
		self.assertEqual(list(self.software.authors.all()), [person])
		self.assertFalse(Person.objects.filter(family_name="Ng").exists())

	def test_submission_api_does_not_resplit(self):
		person = Person.objects.create(given_name="Maria de", family_name="Souza", identifier=self.ORCID)

		response = self._post(authors=[
			{"givenName": "Maria", "familyName": "de Souza", "identifier": self.ORCID},
		])

		self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
		person.refresh_from_db()
		self.assertEqual((person.given_name, person.family_name), ("Maria de", "Souza"))


class PersonSelectorTests(SharedRowTestCase):
	"""Explicit PATCH selection may enrich a shared author in one request."""

	@classmethod
	def setUpTestData(cls):
		super().setUpTestData()
		cls.person = Person.objects.create(given_name="Maria de", family_name="Souza", identifier="")
		cls.other = Software.objects.create(software_name="Other Software")
		cls.other.authors.set([cls.person])
		cls.existing = Person.objects.create(given_name="Ann", family_name="Lee")
		cls.removed = Person.objects.create(given_name="Pat", family_name="Smith")
		cls.software.authors.set([cls.existing, cls.removed])
		cls.affiliation = Organization.objects.create(name="Original Institute")
		cls.person.affiliation.add(cls.affiliation)
		cls.history = SubmissionInfo.objects.create(software=cls.software, submission_date=timezone.now())

	def _author(self, **fields):
		return {
			"personId": str(self.person.pk),
			"givenName": "Maria",
			"familyName": "de Souza",
			"identifier": self.ORCID,
			**fields,
		}

	def _snapshot(self):
		return {
			model.__name__: list(model.objects.order_by("pk").values())
			for model in (
				Software, Person, Organization, SubmissionInfo,
				Software.authors.through, Person.affiliation.through,
			)
		}

	def test_adds_and_enriches_shared_person_in_one_patch(self):
		people_before = Person.objects.count()
		response = self._patch({"authors": [
			self._author(affiliation=[{"name": "Added Institute"}]),
			{"givenName": "Ann", "familyName": "Lee"},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		self.person.refresh_from_db()
		self.assertEqual(self.person.identifier, self.ORCID)
		self.assertEqual((self.person.given_name, self.person.family_name), ("Maria", "de Souza"))
		self.assertEqual(list(self.software.authors.all()), [self.person, self.existing])
		self.assertEqual(list(self.other.authors.all()), [self.person])
		self.assertEqual(Person.objects.count(), people_before)
		self.assertEqual(set(self.person.affiliation.values_list("name", flat=True)),
			{"Original Institute", "Added Institute"})

	def test_namesakes_do_not_interfere_with_selection(self):
		namesakes = [Person.objects.create(given_name="Maria", family_name="de Souza", identifier="") for _ in range(2)]
		self.software.authors.set(namesakes)
		people_before = Person.objects.count()

		response = self._patch({"authors": [self._author()]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		self.assertEqual(list(self.software.authors.all()), [self.person])
		self.assertEqual(Person.objects.count(), people_before)
		for namesake in namesakes:
			namesake.refresh_from_db()
			self.assertEqual(namesake.identifier, "")

	def test_empty_stored_identifiers_can_be_filled(self):
		for identifier in (None, ""):
			with self.subTest(identifier=identifier):
				Person.objects.filter(pk=self.person.pk).update(identifier=identifier)
				response = self._patch({"authors": [self._author()]})
				self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
				self.person.refresh_from_db()
				self.assertEqual(self.person.identifier, self.ORCID)

	def test_same_identifier_and_omitted_identifier_preserve_selected_row(self):
		Person.objects.filter(pk=self.person.pk).update(identifier=self.ORCID)
		for include_identifier in (True, False):
			with self.subTest(include_identifier=include_identifier):
				author = self._author()
				if not include_identifier:
					del author["identifier"]
				response = self._patch({"authors": [author]})
				self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
				self.person.refresh_from_db()
				self.assertEqual(self.person.identifier, self.ORCID)
				self.assertEqual(list(self.software.authors.all()), [self.person])
				self.assertEqual(list(self.person.affiliation.all()), [self.affiliation])

	def test_resplit_without_identifier(self):
		author = self._author()
		del author["identifier"]
		response = self._patch({"authors": [author]})
		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		self.person.refresh_from_db()
		self.assertEqual((self.person.given_name, self.person.family_name), ("Maria", "de Souza"))
		self.assertEqual(self.person.identifier, "")

	def test_invalid_selectors_never_fall_back_or_create(self):
		# A current name match must not rescue a bad explicit selector.
		self.software.authors.set([self.person])
		before = self._snapshot()
		for selector in (None, "", " ", "not-a-uuid", str(uuid.uuid4()), 1, True, {}, []):
			with self.subTest(selector=selector):
				response = self._patch({"authors": [self._author(personId=selector)]})
				self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
				self.assertIn("personId", response.data)
				self.assertEqual(self._snapshot(), before)

	def test_full_name_must_be_the_same_words_in_order(self):
		before = self._snapshot()
		for given, family in (("Mary", "de Souza"), ("Souza", "Maria de"), ("Maria", "de Sousa")):
			with self.subTest(given=given, family=family):
				response = self._patch({"authors": [self._author(givenName=given, familyName=family)]})
				self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
				self.assertIn("stored as 'Maria de Souza'", response.data["personId"])
				self.assertEqual(self._snapshot(), before)

	def test_spelling_differences_take_the_sent_names(self):
		for given, family in (("Maria", "De Souza"), ("Maria", "de-Souza"), ("María", "de Souza")):
			with self.subTest(given=given, family=family):
				response = self._patch({"authors": [self._author(givenName=given, familyName=family)]})
				self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
				self.person.refresh_from_db()
				self.assertEqual((self.person.given_name, self.person.family_name), (given, family))

	def test_sent_names_with_fewer_accents_are_not_applied(self):
		person = Person.objects.create(given_name="José", family_name="García")
		response = self._patch({"authors": [
			{"personId": str(person.pk), "givenName": "Jose", "familyName": "Garcia", "identifier": self.ORCID},
		]})
		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		person.refresh_from_db()
		self.assertEqual((person.given_name, person.family_name, person.identifier), ("José", "García", self.ORCID))

	def test_name_and_identifier_validation_still_applies(self):
		before = self._snapshot()
		for fields in ({"givenName": "", "familyName": "Maria de Souza"}, {"givenName": None},
			{"givenName": []}, {"familyName": ""}, {"familyName": None},
			{"identifier": "not-a-url"}, {"identifier": 1}):
			with self.subTest(fields=fields):
				response = self._patch({"authors": [self._author(**fields)]})
				self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
				self.assertEqual(self._snapshot(), before)

	def test_selected_blank_given_name_can_be_reused(self):
		person = Person.objects.create(given_name="", family_name="Tiger")
		for include_given in (True, False):
			with self.subTest(include_given=include_given):
				author = {"personId": str(person.pk), "familyName": "Tiger", "identifier": self.ORCID}
				if include_given:
					author["givenName"] = ""
				response = self._patch({"authors": [author]})
				self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
				self.assertEqual(list(self.software.authors.all()), [person])
				person.refresh_from_db()
				self.assertEqual(person.given_name, "")
				self.assertEqual(person.identifier, self.ORCID)

	def test_different_stored_identifier_is_rejected(self):
		Person.objects.filter(pk=self.person.pk).update(identifier=self.OTHER_ORCID)
		before = self._snapshot()
		response = self._patch({"authors": [self._author()]})
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
		self.assertIn("identifier", response.data)
		self.assertEqual(self._snapshot(), before)

	def test_identifier_held_by_another_person_is_rejected(self):
		Person.objects.create(given_name="Maria", family_name="de Souza", identifier=self.ORCID)
		# Also reject an identifier duplicated in pre-existing rows.
		for stored in ("", self.ORCID):
			with self.subTest(stored=stored):
				Person.objects.filter(pk=self.person.pk).update(identifier=stored)
				before = self._snapshot()
				response = self._patch({"authors": [self._author()]})
				self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
				self.assertIn("identifier", response.data)
				self.assertEqual(self._snapshot(), before)

	def test_post_rejects_selector_including_empty_values(self):
		before = self._snapshot()
		for selector in (str(self.person.pk), None, ""):
			with self.subTest(selector=selector):
				response = self._post(authors=[self._author(personId=selector)])
				self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
				self.assertIn("personId", response.data)
				self.assertEqual(self._snapshot(), before)

	def test_selector_does_not_bypass_patch_authentication(self):
		before = self._snapshot()
		response = self.client.patch(f"/api/data/software/{self.software.pk}/",
			data={"authors": [self._author()]}, format="json")
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
		self.assertEqual(self._snapshot(), before)

	def test_failure_rolls_back_enrichment_relations_scalars_and_history(self):
		before = self._snapshot()
		for fail_later_field in (False, True):
			with self.subTest(fail_later_field=fail_later_field):
				payload = {
					"description": "Changed description",
					"publisher": {"name": "New Publisher"},
					"authors": [self._author(affiliation=[{"name": "New Institute"}])],
				}
				if fail_later_field:
					payload["programmingLanguage"] = ["Unknown language"]
				else:
					payload["authors"].append(self._author(personId=str(self.existing.pk)))
				response = self._patch(payload)
				self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
				self.assertEqual(self._snapshot(), before)

	def test_selected_person_listed_twice_rejected(self):
		before = self._snapshot()
		for second in (
			self._author(),
			{"givenName": "Maria", "familyName": "de Souza", "identifier": self.ORCID},
			{"givenName": "Maria", "familyName": "de Souza"},
		):
			with self.subTest(second=second):
				response = self._patch({"authors": [self._author(), second]})
				self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.data)
				self.assertIn("authors", response.data)
				self.assertEqual(self._snapshot(), before)


class AwardRowTests(SharedRowTestCase):
	"""How award items resolve to Award rows."""

	def test_award_funder_set_on_new_award(self):
		response = self._patch({"award": [
			{"name": "HSR grant", "identifier": "80NSSC21K0306", "funder": self.NASA},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		award = self.software.award.get()
		self.assertEqual(award.identifier, "80NSSC21K0306")
		self.assertEqual(award.funder.identifier, self.NASA["identifier"])

	def test_award_funder_fills_existing_award_without_one(self):
		award = Award.objects.create(name="HSR grant", identifier="80NSSC21K0306")

		response = self._patch({"award": [
			{"name": "HSR grant", "identifier": "80NSSC21K0306", "funder": self.NASA},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		award.refresh_from_db()
		self.assertEqual(award.funder.identifier, self.NASA["identifier"])
		self.assertEqual(list(self.software.award.all()), [award])

	def test_award_funder_never_replaces_a_different_funder(self):
		other = Organization.objects.create(name="Other Agency")
		award = Award.objects.create(name="HSR grant", identifier="80NSSC21K0306", funder=other)

		response = self._patch({"award": [
			{"name": "HSR grant", "identifier": "80NSSC21K0306", "funder": self.NASA},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		award.refresh_from_db()
		self.assertEqual(award.funder, other)

	def test_award_name_over_128_characters_rejected(self):
		awards = [{"name": "x" * 129, "identifier": "80NSSC21K0306"}]
		for request in (lambda: self._patch({"award": awards}), lambda: self._post(award=awards)):
			response = request()

			self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
			self.assertIn("award.name", response.data)
		self.assertFalse(Award.objects.exists())

	def test_award_funder_must_be_an_object(self):
		response = self._patch({"award": [
			{"name": "HSR grant", "identifier": "80NSSC21K0306", "funder": "NASA"},
		]})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("award.funder", response.data)

	def test_submission_api_accepts_award_funder(self):
		response = self._post(award=[{"name": "HSR grant", "funder": self.NASA}])

		self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
		created = Software.objects.get(software_name="Created via API")
		self.assertEqual(created.award.get().funder.identifier, self.NASA["identifier"])

	def test_submission_api_leaves_existing_awards_unchanged(self):
		by_number = Award.objects.create(name="HSR grant", identifier="80NSSC21K0306")
		by_name = Award.objects.create(name="HTM grant")
		self.software.award.set([by_number, by_name])

		response = self._post(award=[
			{"name": "HSR grant", "identifier": "80NSSC21K0306", "funder": self.NASA},
			{"name": "htm grant", "funder": self.NASA},
		])

		self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
		for award in (by_number, by_name):
			award.refresh_from_db()
			self.assertIsNone(award.funder)
		created = Software.objects.get(software_name="Created via API")
		self.assertEqual(set(created.award.all()), {by_number, by_name})


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

	def test_subject_of_is_emitted_without_a_version(self):
		"""The catalog record exists whether or not the software has a version."""
		self.assertFalse(self.software.version.exists())
		subject_of = self._jsonld(self.software)["subjectOf"]
		self.assertEqual(subject_of["@type"], ["CreativeWork", "dcat:CatalogRecord"])
		self.assertTrue(subject_of["dateModified"].startswith("2025-01-01"))

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

	def _post_edit(self, queue_item):
		return self.client.post(
			f"/curate/edit_submission/submit_data/{queue_item.id}/",
			data=json.dumps(self._form_dict("Should not persist")),
			content_type="application/json",
		)

	def test_edit_link_failure_midway_rolls_back_metadata(self):
		from unittest import mock

		queue_item = SoftwareEditQueue.create(self.software)
		# Raises after the parser's first save has written the new name.
		with mock.patch(
			"website.data_parser.apply_related_observatories",
			side_effect=RuntimeError("boom"),
		) as failing_step:
			response = self._post_edit(queue_item)
		failing_step.assert_called_once()
		self.assertEqual(response.status_code, 500)
		self.software.refresh_from_db()
		self.assertEqual(self.software.software_name, "Stamped")
		self.assertIsNone(self.software.date_modified)

	def test_edit_link_failure_after_final_save_rolls_back_stamp(self):
		from unittest import mock
		from . import data_parser

		def parse_then_fail(*args, **kwargs):
			data_parser.handle_submission_data(*args, **kwargs)
			raise RuntimeError("boom after the final save")

		queue_item = SoftwareEditQueue.create(self.software)
		with mock.patch(
			"website.views.edit_submission.handle_submission_data",
			side_effect=parse_then_fail,
		) as wrapped:
			response = self._post_edit(queue_item)
		wrapped.assert_called_once()
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
