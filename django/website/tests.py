import datetime
import json
import re
import uuid

from django.urls import reverse
from django.test import SimpleTestCase, TestCase

from .models import (
	DataInput,
	FunctionCategory,
	ProgrammingLanguage,
	Region,
	Software,
	SoftwareVersion,
	VerifiedSoftware,
)
from .util import build_software_filter_query, shorten_software_filter_value

FILTER_CASES = [
	("data_sources",           DataInput,            "a1f8de3a-1bde-4995-94e5-e88e841a62a6", "ofjeOhvds"),
	("related_region",         Region,               "b450b02c-ac3e-466e-b3a1-70040b169562", "tFCwLKwr"),
	("programming_language",   ProgrammingLanguage,  "1b6ddaa6-6885-46b3-b59a-ea119e61bd74", "G23apmip"),
	("software_functionality", FunctionCategory,     "332b6567-bdd1-4132-a0c5-532e78b5538c", "MytlZ73f"),
]


class SoftwareFilterEncodingTests(SimpleTestCase):
	def test_tokens_match_frontend_encoding(self):
		for field, _, uid_str, expected_token in FILTER_CASES:
			with self.subTest(field=field):
				self.assertEqual(
					shorten_software_filter_value(field, uuid.UUID(uid_str)),
					expected_token,
				)

	def test_homepage_filter_urls(self):
		for field, model_cls, uid_str, _ in FILTER_CASES:
			with self.subTest(model=model_cls.__name__):
				obj = model_cls(id=uuid.UUID(uid_str), name="test")
				self.assertEqual(
					obj.get_homepage_filter_url(),
					f"/?{build_software_filter_query(field, obj.id)}",
				)


class SoftwareFunctionalityOrderingTests(TestCase):
	def test_functionality_choice_labels_include_parent_once(self):
		data_visualization = FunctionCategory.objects.create(name="Data Visualization")
		spectrogram = FunctionCategory.objects.create(name="Spectrogram")
		mission_related = FunctionCategory.objects.create(name="Mission-related")
		analysis = FunctionCategory.objects.create(name="Analysis")

		data_visualization.children.add(spectrogram)
		mission_related.children.add(analysis)

		self.assertEqual(
			spectrogram.get_choice().name,
			"Data Visualization: Spectrogram",
		)
		self.assertEqual(
			analysis.get_choice().name,
			"Mission-related: Analysis",
		)

	def test_functionality_groups_stay_together_without_inserting_parents(self):
		names = [
			"Data Visualization",
			"Line Plots",
			"Spectrogram",
			"Models and Simulations",
			"Data Processing and Analysis",
			"Analysis",
		]
		categories = {
			name: FunctionCategory.objects.create(name=name)
			for name in names
		}
		categories["Data Visualization"].children.add(
			categories["Line Plots"], categories["Spectrogram"]
		)
		categories["Data Processing and Analysis"].children.add(categories["Analysis"])

		def ordered_names(selected: list[str]) -> list[str]:
			software = Software.objects.create(software_name="Test Software")
			software.software_functionality.set([categories[name] for name in selected])
			return [
				func.name
				for func in software.get_ordered_software_functionality()
			]

		self.assertEqual(
			ordered_names(
				[
					"Data Visualization",
					"Models and Simulations",
					"Data Processing and Analysis",
					"Analysis",
					"Line Plots",
					"Spectrogram",
				]
			),
			[
				"Data Visualization",
				"Line Plots",
				"Spectrogram",
				"Models and Simulations",
				"Data Processing and Analysis",
				"Analysis",
			],
		)
		self.assertEqual(
			ordered_names(["Line Plots", "Analysis"]),
			["Line Plots", "Analysis"],
		)


class SoftwareDetailJsonLdTests(TestCase):
	def _publish_software(self, **kwargs) -> Software:
		software = Software.objects.create(**kwargs)
		VerifiedSoftware.create_verified(software)
		return software

	def _jsonld_scripts(self, html: str) -> list[str]:
		return re.findall(
			r'<script type="application/ld\+json">(.*?)</script>',
			html,
			re.DOTALL,
		)

	def test_software_detail_embeds_jsonld_in_head(self):
		software = self._publish_software(
			software_name="Test Software",
			description="Software for testing JSON-LD landing page metadata.",
			code_repository_url="https://example.com/test-software",
			publication_date=datetime.date(2024, 1, 2),
		)
		version = SoftwareVersion.objects.create(
			number="1.0.0",
			release_date=datetime.date(2024, 2, 3),
			version_pid="https://doi.org/10.1234/test-software.v1",
		)
		software.version.add(version)

		uuid_url = reverse("website:software_detail", kwargs={"pk": software.pk})
		url = software.get_absolute_url()
		redirect_response = self.client.get(uuid_url)
		self.assertEqual(redirect_response.status_code, 302)
		self.assertEqual(redirect_response["Location"], url)

		response = self.client.get(url)

		self.assertEqual(response.status_code, 200)
		html = response.content.decode()
		scripts = self._jsonld_scripts(html)
		self.assertEqual(len(scripts), 1)
		self.assertLess(
			html.index('<script type="application/ld+json">'),
			html.index("</head>"),
		)

		data = json.loads(scripts[0])
		api_response = self.client.get(
			f"/api/view/software/{software.pk}/?view=jsonld"
		)
		self.assertEqual(api_response.status_code, 200)
		self.assertEqual(data, api_response.json())
		self.assertIn("@context", data)
		self.assertEqual(
			data["@type"],
			["SoftwareSourceCode", "SoftwareApplication"],
		)
		self.assertEqual(data["name"], "Test Software")
		self.assertEqual(
			data["description"],
			"Software for testing JSON-LD landing page metadata.",
		)
		self.assertEqual(
			data["subjectOf"]["contentUrl"],
			f"http://testserver{url}",
		)

	def test_software_detail_jsonld_escapes_script_breakout(self):
		description = (
			'Break </script><script>alert("x")</script> & keep <tag>'
		)
		software = self._publish_software(
			software_name="Escaping Test",
			description=description,
		)

		url = software.get_absolute_url()
		response = self.client.get(url)

		self.assertEqual(response.status_code, 200)
		html = response.content.decode()
		scripts = self._jsonld_scripts(html)
		self.assertEqual(len(scripts), 1)
		self.assertNotIn("</script>", scripts[0])
		self.assertNotIn("<tag>", scripts[0])
		self.assertIn("\\u003C/script\\u003E", scripts[0])
		self.assertIn("\\u0026", scripts[0])

		data = json.loads(scripts[0])
		self.assertEqual(data["description"], description)


class SoftwareApiSlugLookupTests(TestCase):
	"""Slug-keyed lookups on /api/view/ and /api/data/ resolve or 404."""

	@classmethod
	def setUpTestData(cls):
		cls.software = Software.objects.create(
			software_name="PyMap3D",
			code_repository_url="https://example.com/pymap3d",
		)
		cls.verified = VerifiedSoftware.create_verified(cls.software)

	def test_slug_resolves_to_software(self):
		self.assertEqual(self.verified.slug, "pymap3d")
		response = self.client.get("/api/view/software/pymap3d/?view=jsonld")
		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.json()["name"], "PyMap3D")

	def test_unknown_slug_returns_404(self):
		for path in (
			"/api/view/software/no-such-software/",
			"/api/view/software/no-such-software/?view=jsonld",
			"/api/data/software/no-such-software/",
		):
			with self.subTest(path=path):
				self.assertEqual(self.client.get(path).status_code, 404)

	def test_display_name_that_is_not_the_slug_returns_404(self):
		"""The list endpoint's display name is not a valid lookup key.

		Only the slug is. A caller substituting the name used to get a 500,
		which read as an outage rather than a wrong key.
		"""
		response = self.client.get("/api/view/software/PyMap3D/?view=jsonld")
		self.assertEqual(response.status_code, 404)

	def test_unpublished_software_is_not_reachable_by_slug(self):
		unpublished = Software.objects.create(software_name="Unpublished")
		response = self.client.get(f"/api/view/software/{unpublished.pk}/")
		self.assertEqual(response.status_code, 404)
