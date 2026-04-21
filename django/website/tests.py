import uuid

from django.test import SimpleTestCase, TestCase

from .models import DataInput, FunctionCategory, ProgrammingLanguage, Region, Software
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
