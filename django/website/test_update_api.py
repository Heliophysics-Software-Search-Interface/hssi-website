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
	Curator,
	InstrObsType,
	InstrumentObservatory,
	Keyword,
	License,
	Organization,
	Person,
	RelatedItem,
	RelatedItemType,
	RepoStatus,
	Software,
	SoftwareEditQueue,
	SoftwareVersion,
	SubmissionInfo,
	Submitter,
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
		Software.objects.create(software_name="Other").authors.set([person])
		self.software.authors.set([person])

		response = self._patch({"authors": [
			{"givenName": "Mary", "familyName": "de Souza", "identifier": self.ORCID},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		person.refresh_from_db()
		self.assertEqual((person.given_name, person.family_name), ("Maria de", "Souza"))

	def test_exclusive_identified_author_takes_a_rename(self):
		person = Person.objects.create(given_name="Petr", family_name="Shumate", identifier=self.ORCID)
		self.software.authors.set([person])

		response = self._patch({"authors": [
			{"givenName": "Peter", "familyName": "Shumate", "identifier": self.ORCID},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		person.refresh_from_db()
		self.assertEqual((person.given_name, person.family_name), ("Peter", "Shumate"))

	def test_identified_author_keeps_names_while_a_submitter_or_curator(self):
		submitter = Person.objects.create(given_name="Petr", family_name="Shumate", identifier=self.ORCID)
		Submitter.objects.create(email="petr@example.com", person=submitter)
		curator = Person.objects.create(given_name="Ann", family_name="Le", identifier=self.OTHER_ORCID)
		Curator.objects.create(email="ann@example.com", person=curator)
		self.software.authors.set([submitter, curator])

		response = self._patch({"authors": [
			{"givenName": "Peter", "familyName": "Shumate", "identifier": self.ORCID},
			{"givenName": "Ann", "familyName": "Lee", "identifier": self.OTHER_ORCID},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		submitter.refresh_from_db()
		curator.refresh_from_db()
		self.assertEqual((submitter.given_name, submitter.family_name), ("Petr", "Shumate"))
		self.assertEqual((curator.given_name, curator.family_name), ("Ann", "Le"))

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


class OrganizationRowTests(SharedRowTestCase):
	"""How affiliations, funders and publishers resolve to Organization rows."""

	ROR = "https://ror.org/00example"

	def test_identifier_fills_the_authors_same_name_affiliation(self):
		org = Organization.objects.create(name="Example Observatory")
		author = Person.objects.create(given_name="Ann", family_name="Lee")
		author.affiliation.add(org)
		self.software.authors.set([author])
		orgs_before = Organization.objects.count()

		response = self._patch({"authors": [{
			"givenName": "Ann",
			"familyName": "Lee",
			"affiliation": [{"name": "example observatory", "identifier": self.ROR}],
		}]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		org.refresh_from_db()
		self.assertEqual((org.name, org.identifier), ("Example Observatory", self.ROR))
		self.assertEqual(list(author.affiliation.all()), [org])
		self.assertEqual(Organization.objects.count(), orgs_before)

	def test_identifier_fills_this_records_same_name_funder(self):
		nasa = Organization.objects.create(name="NASA")
		self.software.funder.set([nasa])

		response = self._patch({"funder": [self.NASA]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		nasa.refresh_from_db()
		self.assertEqual(nasa.identifier, self.NASA["identifier"])
		self.assertEqual(list(self.software.funder.all()), [nasa])

	def test_identifier_fills_this_records_same_name_publisher(self):
		zenodo = Organization.objects.create(name="Zenodo")
		self.software.publisher = zenodo
		self.software.save()

		response = self._patch({"publisher": {"name": "Zenodo", "identifier": self.ROR}})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		zenodo.refresh_from_db()
		self.software.refresh_from_db()
		self.assertEqual(zenodo.identifier, self.ROR)
		self.assertEqual(self.software.publisher, zenodo)

	def test_identifier_never_replaces_a_different_identifier(self):
		nasa = Organization.objects.create(name="NASA", identifier=self.ROR)
		self.software.funder.set([nasa])

		response = self._patch({"funder": [self.NASA]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		nasa.refresh_from_db()
		self.assertEqual(nasa.identifier, self.ROR)
		self.assertEqual(self.software.funder.get().identifier, self.NASA["identifier"])

	def test_identifier_ignores_same_name_organizations_not_linked_here(self):
		nasa = Organization.objects.create(name="NASA")

		response = self._patch({"funder": [self.NASA]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		nasa.refresh_from_db()
		self.assertIsNone(nasa.identifier)
		funder = self.software.funder.get()
		self.assertNotEqual(funder.pk, nasa.pk)
		self.assertEqual(funder.identifier, self.NASA["identifier"])

	def test_identifier_held_elsewhere_binds_that_organization(self):
		held = Organization.objects.create(
			name="National Aeronautics and Space Administration",
			identifier=self.NASA["identifier"],
		)
		nasa = Organization.objects.create(name="NASA")
		self.software.funder.set([nasa])

		response = self._patch({"funder": [self.NASA]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		nasa.refresh_from_db()
		self.assertIsNone(nasa.identifier)
		self.assertEqual(list(self.software.funder.all()), [held])

	def test_identifier_fills_nothing_when_two_organizations_match(self):
		twins = [Organization.objects.create(name="NASA"), Organization.objects.create(name="nasa")]
		self.software.funder.set(twins)

		response = self._patch({"funder": [self.NASA]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		for twin in twins:
			twin.refresh_from_db()
			self.assertIsNone(twin.identifier)
		funder = self.software.funder.get()
		self.assertNotIn(funder, twins)
		self.assertEqual(funder.identifier, self.NASA["identifier"])

	def test_submission_api_does_not_fill_affiliations(self):
		org = Organization.objects.create(name="Example Observatory")
		Person.objects.create(given_name="Ada", family_name="Lovelace").affiliation.add(org)

		response = self._post(authors=[{
			"givenName": "Ada",
			"familyName": "Lovelace",
			"affiliation": [{"name": "Example Observatory", "identifier": self.ROR}],
		}])

		self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
		org.refresh_from_db()
		self.assertIsNone(org.identifier)


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

	def test_exclusive_award_takes_the_sent_name(self):
		award = Award.objects.create(name="Grant", identifier="80NSSC21K0306")
		self.software.award.set([award])

		response = self._patch({"award": [{"name": "HSR grant", "identifier": "80NSSC21K0306"}]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		award.refresh_from_db()
		self.assertEqual(award.name, "HSR grant")

	def test_shared_award_keeps_its_name_unless_empty(self):
		titled = Award.objects.create(name="Grant", identifier="80NSSC21K0306")
		untitled = Award.objects.create(name="", identifier="24-HTM24-0022")
		Software.objects.create(software_name="Other").award.set([titled, untitled])
		self.software.award.set([titled, untitled])

		response = self._patch({"award": [
			{"name": "HSR grant", "identifier": "80NSSC21K0306"},
			{"name": "HTM grant", "identifier": "24-HTM24-0022"},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		titled.refresh_from_db()
		untitled.refresh_from_db()
		self.assertEqual((titled.name, untitled.name), ("Grant", "HTM grant"))

	def test_submission_api_does_not_rename_awards(self):
		award = Award.objects.create(name="Grant", identifier="80NSSC21K0306")

		response = self._post(award=[{"name": "HSR grant", "identifier": "80NSSC21K0306"}])

		self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
		award.refresh_from_db()
		self.assertEqual(award.name, "Grant")

	def test_award_name_over_128_characters_rejected(self):
		awards = [{"name": "x" * 129, "identifier": "80NSSC21K0306"}]
		for request in (lambda: self._patch({"award": awards}), lambda: self._post(award=awards)):
			response = request()

			self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
			self.assertIn("award.name", response.data)
		self.assertFalse(Award.objects.exists())

	def test_award_funder_fills_this_records_same_name_funder(self):
		nasa = Organization.objects.create(name="NASA")
		self.software.funder.set([nasa])
		orgs_before = Organization.objects.count()

		response = self._patch({"award": [
			{"name": "HSR grant", "identifier": "80NSSC21K0306", "funder": self.NASA},
		]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		nasa.refresh_from_db()
		self.assertEqual(nasa.identifier, self.NASA["identifier"])
		self.assertEqual(self.software.award.get().funder, nasa)
		self.assertEqual(Organization.objects.count(), orgs_before)

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


class RelatedItemRowTests(SharedRowTestCase):
	"""How publication, dataset and software links resolve to RelatedItem rows."""

	URL = "https://doi.org/10.5281/zenodo.1234567"

	def _item(self, item_type: RelatedItemType) -> RelatedItem:
		return RelatedItem.objects.create(name=self.URL, identifier=self.URL, type=item_type)

	def test_item_linked_only_here_takes_the_fields_type(self):
		item = self._item(RelatedItemType.PUBLICATION)
		self.software.related_datasets.set([item])

		response = self._patch({"relatedDatasets": [self.URL]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		item.refresh_from_db()
		self.assertEqual(item.type, RelatedItemType.DATASET)

	def test_unlinked_item_takes_the_fields_type(self):
		item = self._item(RelatedItemType.SOFTWARE)

		response = self._patch({"relatedPublications": [self.URL]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		item.refresh_from_db()
		self.assertEqual(item.type, RelatedItemType.PUBLICATION)
		self.assertEqual(list(self.software.related_publications.all()), [item])

	def test_item_linked_by_another_record_keeps_its_type(self):
		item = self._item(RelatedItemType.PUBLICATION)
		Software.objects.create(software_name="Other").related_publications.set([item])

		response = self._patch({"relatedDatasets": [self.URL]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		item.refresh_from_db()
		self.assertEqual(item.type, RelatedItemType.PUBLICATION)

	def test_item_this_record_links_as_another_type_keeps_its_type(self):
		item = self._item(RelatedItemType.PUBLICATION)
		self.software.related_publications.set([item])

		response = self._patch({"relatedDatasets": [self.URL]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		item.refresh_from_db()
		self.assertEqual(item.type, RelatedItemType.PUBLICATION)

	def test_items_moved_between_fields_in_one_request_take_their_new_types(self):
		other_url = "https://doi.org/10.5281/zenodo.7654321"
		to_publication = self._item(RelatedItemType.DATASET)
		to_dataset = RelatedItem.objects.create(name=other_url, identifier=other_url, type=RelatedItemType.PUBLICATION)
		self.software.related_datasets.set([to_publication])
		self.software.related_publications.set([to_dataset])

		response = self._patch({"relatedPublications": [self.URL], "relatedDatasets": [other_url]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		to_publication.refresh_from_db()
		to_dataset.refresh_from_db()
		self.assertEqual(to_publication.type, RelatedItemType.PUBLICATION)
		self.assertEqual(to_dataset.type, RelatedItemType.DATASET)

	def test_items_in_fields_not_sent_keep_their_types(self):
		item = self._item(RelatedItemType.PUBLICATION)
		self.software.related_datasets.set([item])

		response = self._patch({"description": "Updated."})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		item.refresh_from_db()
		self.assertEqual(item.type, RelatedItemType.PUBLICATION)

	def test_url_variants_bind_the_stored_item(self):
		variants_by_stored_url = {
			self.URL: [
				"http://doi.org/10.5281/zenodo.1234567",
				"https://doi.org/10.5281/zenodo.1234567/",
				"https://dx.doi.org/10.5281/zenodo.1234567",
				"https://doi.org/10.5281/ZENODO.1234567",
			],
			"http://dx.doi.org/10.5281/ZENODO.7654321/": ["https://doi.org/10.5281/zenodo.7654321"],
			"https://example.com/Docs/": ["http://example.com/Docs"],
		}
		for stored_url, variants in variants_by_stored_url.items():
			item = RelatedItem.objects.create(
				name=stored_url, identifier=stored_url, type=RelatedItemType.PUBLICATION,
			)
			for variant in variants:
				with self.subTest(stored=stored_url, sent=variant):
					response = self._patch({"relatedPublications": [variant]})

					self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
					self.assertEqual(list(self.software.related_publications.all()), [item])
		self.assertEqual(RelatedItem.objects.count(), len(variants_by_stored_url))

	def test_url_path_outside_doi_org_keeps_its_case(self):
		item = RelatedItem.objects.create(
			name="https://example.com/Docs", identifier="https://example.com/Docs",
			type=RelatedItemType.PUBLICATION,
		)

		response = self._patch({"relatedPublications": ["https://example.com/docs"]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		linked = self.software.related_publications.get()
		self.assertNotEqual(linked.pk, item.pk)
		self.assertEqual(linked.identifier, "https://example.com/docs")

	def test_new_item_stores_the_normalized_url(self):
		response = self._patch({"relatedPublications": ["http://dx.doi.org/10.5281/ZENODO.42/"]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		linked = self.software.related_publications.get()
		self.assertEqual(linked.identifier, "https://doi.org/10.5281/zenodo.42")

	def test_submission_api_matches_urls_exactly(self):
		item = self._item(RelatedItemType.PUBLICATION)
		variant = "https://dx.doi.org/10.5281/zenodo.1234567"

		response = self._post(relatedPublications=[variant])

		self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
		linked = Software.objects.get(software_name="Created via API").related_publications.get()
		self.assertNotEqual(linked.pk, item.pk)
		self.assertEqual(linked.identifier, variant)

	def test_submission_api_does_not_retype(self):
		item = self._item(RelatedItemType.SOFTWARE)

		response = self._post(relatedPublications=[self.URL])

		self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
		item.refresh_from_db()
		self.assertEqual(item.type, RelatedItemType.SOFTWARE)


class InstrumentObservatoryRowTests(SharedRowTestCase):
	"""How related instruments and observatories resolve to InstrumentObservatory rows."""

	MAG = "https://spase-metadata.org/NASA/Instrument/ACE/MAG"
	ACE = "https://spase-metadata.org/NASA/Observatory/ACE"

	def _entry(self, identifier: str, instr_type: InstrObsType, abbreviation=None) -> InstrumentObservatory:
		return InstrumentObservatory.objects.create(
			name=identifier.rsplit("/", 1)[1], identifier=identifier, type=instr_type, abbreviation=abbreviation,
		)

	def test_spase_page_url_binds_the_stored_entry(self):
		mag = self._entry(self.MAG, InstrObsType.INSTRUMENT)

		for sent in (f"{self.MAG}.html", f"{self.MAG}/"):
			with self.subTest(sent=sent):
				response = self._patch({"relatedInstruments": [{"name": "MAG", "identifier": sent}]})

				self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
				self.assertEqual(list(self.software.related_instruments.all()), [mag])
		self.assertEqual(InstrumentObservatory.objects.count(), 1)

	def test_entry_of_the_other_type_rejected(self):
		self._entry(self.ACE, InstrObsType.OBSERVATORY)
		instruments = [{"name": "ACE", "identifier": self.ACE}]

		for request in (
			lambda: self._patch({"relatedInstruments": instruments}),
			lambda: self._post(relatedInstruments=instruments),
		):
			response = request()

			self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
			self.assertIn("identifier", response.data)
		self.assertFalse(self.software.related_instruments.exists())

	def test_abbreviation_fills_only_an_empty_one(self):
		mag = self._entry(self.MAG, InstrObsType.INSTRUMENT)
		ace = self._entry(self.ACE, InstrObsType.OBSERVATORY, abbreviation="ACE")

		response = self._patch({
			"relatedInstruments": [{"name": "MAG", "identifier": self.MAG, "abbreviation": "MAG"}],
			"relatedObservatories": [{"name": "ACE", "identifier": self.ACE, "abbreviation": "Advanced Composition Explorer"}],
		})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		mag.refresh_from_db()
		ace.refresh_from_db()
		self.assertEqual((mag.abbreviation, ace.abbreviation), ("MAG", "ACE"))

	def test_entry_stored_as_a_page_url_still_binds(self):
		page = f"{self.ACE}.html"
		ace = self._entry(page, InstrObsType.OBSERVATORY)

		response = self._patch({"relatedObservatories": [{"name": "ACE", "identifier": page}]})

		self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
		self.assertEqual(list(self.software.related_observatories.all()), [ace])
		self.assertEqual(InstrumentObservatory.objects.count(), 1)

		response = self._patch({"relatedInstruments": [{"name": "ACE", "identifier": page}]})

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn("identifier", response.data)

	def test_submission_api_matches_spase_urls_exactly(self):
		mag = self._entry(self.MAG, InstrObsType.INSTRUMENT)

		response = self._post(relatedInstruments=[{"name": "MAG", "identifier": f"{self.MAG}.html", "abbreviation": "MAG"}])

		self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
		linked = Software.objects.get(software_name="Created via API").related_instruments.get()
		self.assertNotEqual(linked.pk, mag.pk)
		self.assertIsNone(linked.abbreviation)


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
